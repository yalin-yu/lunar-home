"""P2 事件场景 — 角色叠加在背景上，文本框在背景底部"""

import base64
import html
import streamlit as st
from pathlib import Path
from engine.config_loader import get_loader
from engine.game_state import GameStateManager
from engine.prompt_builder import PromptBuilder
from engine.ai_client import AIClient
from engine.models import SceneType
from ui.assets import get_scene_background, get_character_sprite, get_background


def _img_b64(path: str | None) -> str:
    """本地图片转 base64 data URI，路径无效返回空字符串"""
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    ext = p.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def render():
    state = st.session_state.game_state
    loader = get_loader()
    chapter = loader.get_chapter(state.chapter_id)

    # 返回按钮
    def _on_back():
        st.session_state.game_state = GameStateManager.navigate_to_page(
            st.session_state.game_state, "P3"
        )
    st.button("← 返回路线图", key="p2_back", on_click=_on_back)

    # ---- 确定当前场景/分支 ----
    if state.current_branch:
        branch_obj = None
        for b in chapter.branches:
            if b.id == state.current_branch:
                branch_obj = b
                break
        if branch_obj is None:
            st.error(f"分支 '{state.current_branch}' 未找到")
            return
        scene_obj = None
        scene_type = SceneType.AI_DIALOGUE
        bg_path = get_background(branch_obj.background)
    else:
        scene_obj = None
        for s in chapter.scenes:
            if s.id == state.current_scene:
                scene_obj = s
                break
        if scene_obj is None:
            st.error(f"场景 '{state.current_scene}' 未找到")
            return
        scene_type = scene_obj.type
        bg_path = get_scene_background(state.current_scene)

    bg_b64 = _img_b64(bg_path)

    # ---- 角色立绘 ----
    sprite_b64 = ""
    if scene_type == SceneType.SCRIPTED_DIALOGUE and scene_obj:
        if state.current_beat_index < len(scene_obj.key_beats):
            beat = scene_obj.key_beats[state.current_beat_index]
            if beat.speaker != "narration":
                sprite_b64 = _img_b64(get_character_sprite(beat.speaker))
    elif scene_type == SceneType.AI_DIALOGUE and branch_obj:
        # AI 对话时显示 NPC 角色立绘
        npc_id = branch_obj.ai_dialogue.responding_character
        sprite_b64 = _img_b64(get_character_sprite(npc_id))

    # ---- 路由 ----
    if scene_type in (SceneType.NARRATION, SceneType.TRANSITION):
        # 太阳风暴特殊处理：旁白结束后进入与柳夜的对话
        if (state.current_scene == "transition_solar_storm"
                and state.current_beat_index >= len(scene_obj.key_beats)):
            _render_solar_storm_dialogue(state, bg_b64, chapter)
        else:
            _render_narration(state, scene_obj, bg_b64, sprite_b64)
    elif scene_type == SceneType.SCRIPTED_DIALOGUE:
        _render_scripted_dialogue(state, scene_obj, bg_b64, sprite_b64)
    elif scene_type == SceneType.AI_DIALOGUE:
        _render_ai_dialogue(state, branch_obj, bg_b64, sprite_b64)


# ==================== 场景 HTML 构建 ====================

def _scene_html(bg_b64: str, sprite_b64: str, text: str,
                speaker: str = "", is_narration: bool = False):
    """构建叠加式场景：背景图(img)+角色立绘+底部半透明文本框。
    使用 <img> 而非 CSS background 避免超大内联 style 触发 Markdown 代码块解析。"""

    # 背景层：用 <img> + object-fit:cover 代替 CSS background:url()
    bg_tag = ""
    if bg_b64:
        bg_tag = (
            '<img src="' + bg_b64 + '" '
            'style="position:absolute;top:0;left:0;width:100%;height:100%;'
            'object-fit:cover;z-index:0;" />'
        )
    bg_color = '#1a1a2e' if not bg_b64 else '#0d0d1a'

    # 角色立绘
    sprite_tag = ""
    if sprite_b64:
        sprite_tag = (
            '<div style="position:absolute;bottom:0;left:50%;'
            'transform:translateX(-50%);z-index:2;">'
            '<img src="' + sprite_b64 + '" style="max-height:50vh;max-width:90vw;" />'
            '</div>'
        )

    # 说话人 & 文字样式
    if is_narration or not speaker:
        speaker_tag = ""
        text_style = "color:#aaa;font-style:italic;text-align:center;font-size:0.95rem;line-height:1.8;"
    else:
        speaker_tag = (
            '<div style="color:#4A90D9;font-weight:bold;font-size:0.85rem;margin-bottom:6px;">'
            + html.escape(speaker) + '</div>'
        )
        text_style = "color:#e0e0e0;font-size:0.95rem;line-height:1.7;"

    # 拼装成单行无缩进 HTML，避免 Markdown 代码块解析
    html_str = (
        '<div style="position:relative;width:100%;min-height:70vh;'
        'background-color:' + bg_color + ';'
        'border-radius:8px;overflow:hidden;margin-bottom:8px;">'
        + bg_tag +
        '<div style="position:absolute;bottom:0;left:0;right:0;'
        'background:rgba(0,0,0,0.82);padding:18px 20px;'
        'border-top:1px solid rgba(255,255,255,0.1);z-index:3;">'
        + speaker_tag +
        '<div style="' + text_style + '">' + html.escape(text) + '</div>'
        '</div>'
        + sprite_tag +
        '</div>'
    )
    st.markdown(html_str, unsafe_allow_html=True)


# ==================== 各类型渲染 ====================

def _render_narration(state, scene_obj, bg_b64, sprite_b64):
    """旁白 / 转场"""
    # 已播完所有 beat → 显示结束提示
    if state.current_beat_index >= len(scene_obj.key_beats):
        if scene_obj.next:
            st.session_state.game_state = state.model_copy(update={
                "current_scene": scene_obj.next,
                "current_beat_index": 0,
            })
            st.rerun()
        else:
            _scene_html(bg_b64, sprite_b64, "—— 本节结束 ——", is_narration=True)
            def _to_map():
                st.session_state.game_state = GameStateManager.navigate_to_page(
                    st.session_state.game_state, "P3"
                )
            st.button("← 返回路线图", key="narration_end_back",
                      on_click=_to_map, use_container_width=True)
        return

    beat = scene_obj.key_beats[state.current_beat_index]
    _scene_html(bg_b64, sprite_b64, beat.text, is_narration=True)

    st.caption(
        f"场景: {state.current_scene}  |  "
        f"节拍: {state.current_beat_index + 1}/{len(scene_obj.key_beats)}"
    )

    def _advance():
        st.session_state.game_state = GameStateManager.advance_beat(
            st.session_state.game_state
        )

    st.button("继续 ▸", key="narration_continue",
              on_click=_advance, use_container_width=True)


def _render_scripted_dialogue(state, scene_obj, bg_b64, sprite_b64):
    """脚本对话"""
    loader = get_loader()
    if state.current_beat_index >= len(scene_obj.key_beats):
        if scene_obj.decision:
            _render_decision(state, scene_obj.decision, bg_b64, sprite_b64)
        elif scene_obj.next:
            st.session_state.game_state = state.model_copy(update={
                "current_scene": scene_obj.next,
                "current_beat_index": 0,
            })
            st.rerun()
        else:
            _scene_html(bg_b64, sprite_b64, "—— 本节结束 ——", is_narration=True)
            def _to_map():
                st.session_state.game_state = GameStateManager.navigate_to_page(
                    st.session_state.game_state, "P3"
                )
            st.button("← 返回路线图", key="dialogue_end_back",
                      on_click=_to_map, use_container_width=True)
        return

    beat = scene_obj.key_beats[state.current_beat_index]
    if beat.speaker == "narration":
        speaker_name = "旁白"
    else:
        # 从角色配置中解析中文名
        try:
            char = loader.get_character(beat.speaker)
            speaker_name = char.name_cn
        except KeyError:
            speaker_name = beat.speaker  # fallback

    _scene_html(bg_b64, sprite_b64, beat.text, speaker=speaker_name)

    st.caption(
        f"场景: {state.current_scene}  |  "
        f"节拍: {state.current_beat_index + 1}/{len(scene_obj.key_beats)}"
    )

    def _advance():
        st.session_state.game_state = GameStateManager.advance_beat(
            st.session_state.game_state
        )

    st.button("继续 ▸", key="dialogue_continue",
              on_click=_advance, use_container_width=True)


def _render_decision(state, decision, bg_b64, sprite_b64=""):
    """决策点（对话播完后触发）— 含选择后果过渡"""

    # 检查是否有待确认的后果
    pending_key = f"consequence_{decision.id}"
    if pending_key in st.session_state:
        pending = st.session_state[pending_key]
        _scene_html(bg_b64, sprite_b64, pending["consequence"], speaker="你的选择")
        st.caption("—— 这将改变故事的走向 ——")

        def _confirm():
            st.session_state.pop(pending_key, None)
            st.session_state.game_state = GameStateManager.select_option(
                st.session_state.game_state, pending["opt_id"], pending["leads_to"]
            )
        st.button("继续 ▸", key=f"consequence_confirm_{decision.id}",
                  on_click=_confirm, use_container_width=True)
        return

    # 正常决策界面
    _scene_html(bg_b64, "", decision.prompt_context, speaker="")

    for opt in decision.options:
        def _make_callback(opt_id=opt.id, leads_to=opt.leads_to, consequence=opt.consequence):
            def _select():
                st.session_state[pending_key] = {
                    "opt_id": opt_id,
                    "leads_to": leads_to,
                    "consequence": consequence or f"你选择了「{opt_id}」",
                }
            return _select

        st.button(opt.label, key=f"opt_{opt.id}",
                  on_click=_make_callback(), use_container_width=True)


# ==================== AI 对话（分支） ====================

def _render_ai_dialogue(state, branch_obj, bg_b64, sprite_b64):
    """AI 实时对话 — 统一交互模式"""
    loader = get_loader()
    chapter = loader.get_chapter(state.chapter_id)
    ai_config = branch_obj.ai_dialogue
    npc = loader.get_character(ai_config.responding_character)

    # 构建 system prompt（缓存）
    sys_key = f"sys_{state.current_branch}"
    if sys_key not in st.session_state:
        prompt_builder = PromptBuilder()
        st.session_state[sys_key] = prompt_builder.build(
            situation_prompt=ai_config.situation_prompt,
            responding_character_id=ai_config.responding_character,
            supporting_character_ids=ai_config.supporting_characters,
            chapter_id=state.chapter_id,
        )
    system_prompt = st.session_state[sys_key]

    # 初始化：首次进入时自动生成 NPC 开场白
    init_key = f"ai_opening_{state.current_branch}"
    if init_key not in st.session_state and not state.dialogue_history:
        st.session_state[init_key] = True
        client = AIClient()
        opening = client.chat(system_prompt, [
            {"role": "user", "content": "（场景开始，请以你的角色身份主动开口说话，推进对话）"}
        ])
        new_state = GameStateManager.add_dialogue(
            state, ai_config.responding_character,
            npc.name_cn, opening, is_ai=True
        )
        st.session_state.game_state = new_state
        # 生成两个 LLM 建议
        _gen_llm_suggestions(state.current_branch, system_prompt, new_state.dialogue_history, npc.name_cn)
        st.rerun()

    # 显示分支信息
    st.caption(f"**{branch_obj.title}** — {branch_obj.subtitle}")
    st.caption(f"回合 {state.turn_count}/{ai_config.max_turns}")

    # 对话历史：第一条 NPC 消息用背景，后续用纯对话框
    is_first_npc = True
    for msg in state.dialogue_history:
        is_player = msg.speaker_id == "player"
        if is_player:
            with st.container(border=True):
                st.caption(f"**{msg.speaker_name}（你）**")
                st.write(msg.text)
        else:
            if is_first_npc:
                _scene_html(bg_b64, sprite_b64, msg.text, speaker=msg.speaker_name)
                is_first_npc = False
            else:
                with st.container(border=True):
                    st.caption(f"**{msg.speaker_name}**")
                    st.write(msg.text)

    # ---- 检查是否已达轮数上限 ----
    if ai_config.success_conditions and state.turn_count >= ai_config.max_turns:
        player_msgs = [m.text for m in state.dialogue_history if m.speaker_id == "player"]
        hit = _check_success_keywords(player_msgs, ai_config)
        if not hit:
            _handle_branch_failure(state, branch_obj, chapter, bg_b64)
            return

    # ---- 统一交互区 ----
    _render_unified_input(state.current_branch, state, branch_obj, ai_config,
                          npc, system_prompt, chapter, bg_b64, sprite_b64, is_branch=True)


def _render_unified_input(dialogue_id, state, branch_obj, ai_config, npc,
                          system_prompt, chapter, bg_b64, sprite_b64,
                          is_branch=True):
    """统一的对话交互：快速跳过 + LLM建议1/2（三行） + 自由文本"""

    # 检查是否正在显示跳过旁白
    skip_narr_key = f"skip_narration_{dialogue_id}"
    if skip_narr_key in st.session_state:
        narration = st.session_state[skip_narr_key]
        _scene_html(bg_b64, sprite_b64, narration, speaker="旁白", is_narration=True)
        def _confirm_skip():
            st.session_state.pop(skip_narr_key, None)
            if is_branch:
                new_state = GameStateManager.mark_branch_complete(state, state.current_branch)
                # 检查该分支是否触发结局（如 B3 → ending_success）
                ending = None
                for e in chapter.endings:
                    if e.trigger_branch == state.current_branch:
                        ending = e
                        break
                if ending:
                    new_state = GameStateManager.trigger_ending(new_state, ending.id)
                else:
                    new_state = GameStateManager.navigate_to_page(new_state, "P3")
                st.session_state.game_state = new_state
            else:
                st.session_state["solar_storm_dialogue"]["ended"] = True
        st.button("继续 ▸", key=f"skip_narr_confirm_{dialogue_id}",
                  on_click=_confirm_skip, use_container_width=True)
        return

    input_key = f"text_input_{dialogue_id}"
    sugg_key = f"suggestions_{dialogue_id}"

    # ---- 三行按钮布局 ----
    # 第一行：快速跳过
    def _skip():
        _gen_skip_narration(dialogue_id, system_prompt, ai_config, npc, is_branch, state, chapter)
    st.button("⚡ 快速跳过对话", key=f"skip_{dialogue_id}",
              on_click=_skip, use_container_width=True)

    # 第二行 & 第三行：LLM 建议
    suggestions = st.session_state.get(sugg_key, ["", ""])
    s1 = suggestions[0] if len(suggestions) > 0 else ""
    s2 = suggestions[1] if len(suggestions) > 1 else ""

    btn1_text = s1[:35] if s1 else "（正在生成建议...）"
    btn1_disabled = not s1 or s1.startswith("（")

    def _use_s1():
        _process_and_regenerate(state, branch_obj, ai_config, npc,
                                system_prompt, chapter, s1,
                                is_branch, dialogue_id)
    st.button(f"💬 {btn1_text}", key=f"sugg1_{dialogue_id}",
              on_click=_use_s1, use_container_width=True, disabled=btn1_disabled)

    btn2_text = s2[:35] if s2 else "（正在生成建议...）"
    btn2_disabled = not s2 or s2.startswith("（")

    def _use_s2():
        _process_and_regenerate(state, branch_obj, ai_config, npc,
                                system_prompt, chapter, s2,
                                is_branch, dialogue_id)
    st.button(f"💬 {btn2_text}", key=f"sugg2_{dialogue_id}",
              on_click=_use_s2, use_container_width=True, disabled=btn2_disabled)

    # ---- 自由文本输入 ----
    col_input, col_send = st.columns([4, 1])
    with col_input:
        st.text_area(
            "你的回应", key=input_key, height=68,
            placeholder="输入你想说的话...",
            label_visibility="collapsed",
        )
    with col_send:
        def _send():
            txt = st.session_state.get(input_key, "").strip()
            if txt:
                _process_and_regenerate(state, branch_obj, ai_config, npc,
                                        system_prompt, chapter, txt,
                                        is_branch, dialogue_id)
        st.button("发送 ▸", key=f"send_{dialogue_id}",
                  on_click=_send, use_container_width=True)


def _gen_skip_narration(dialogue_id, system_prompt, ai_config, npc, is_branch, state, chapter):
    """生成跳过对话的旁白总结"""
    skip_narr_key = f"skip_narration_{dialogue_id}"

    # 获取分支预设结局描述
    branch_ending = ""
    if is_branch and hasattr(ai_config, 'success_conditions') and chapter:
        for b in chapter.branches:
            if b.id == state.current_branch:
                branch_ending = b.branch_ending_narration
                break

    ending_hint = f"\n这个故事预设的走向是：{branch_ending}" if branch_ending else ""
    client = AIClient()
    prompt = (
        f"请以旁白口吻，用2-3段文字总结如果秦洛与{npc.name_cn}的对话达成共识后的后续发展。"
        f"要符合世界观设定，保持叙述风格。{ending_hint}"
    )
    narration = client.chat(system_prompt, [{"role": "user", "content": prompt}])
    st.session_state[skip_narr_key] = narration or "对话结束，秦洛继续前行。"
    st.rerun()


def _process_and_regenerate(state, branch_obj, ai_config, npc, system_prompt,
                            chapter, text, is_branch, dialogue_id):
    """处理玩家回合 → AI 回复 → 重新生成建议"""
    if is_branch:
        action, new_state_or_none = _process_player_turn(
            state, branch_obj, ai_config, npc, system_prompt, text
        )
        if action == "rerun":
            # _process_player_turn already set game_state and called rerun internally
            return
        if action == "done":
            # 已导航离开（成功/失败），无需再生建议
            return
        # action == "continue": 对话继续，new_state 是更新后的状态
        st.session_state.game_state = new_state_or_none
        _gen_llm_suggestions(dialogue_id, system_prompt,
                            new_state_or_none.dialogue_history, npc.name_cn)
        st.rerun()
    else:
        storm = st.session_state.get("solar_storm_dialogue", {})
        _storm_process_turn_inner(storm, system_prompt, npc, text)
        if not storm.get("ended"):
            history = [{"speaker_id": "npc" if m["role"] == "npc" else "player",
                       "speaker_name": npc.name_cn if m["role"] == "npc" else "秦洛",
                       "text": m["text"]}
                       for m in storm["history"]]
            _gen_llm_suggestions(dialogue_id, system_prompt, history, npc.name_cn)
        st.rerun()


def _gen_llm_suggestions(dialogue_id, system_prompt, dialogue_history, npc_name):
    """用 LLM 生成两个玩家回应建议（不触发 rerun）"""
    import re
    sugg_key = f"suggestions_{dialogue_id}"
    client = AIClient()
    history_text = "\n".join([
        f"{'玩家' if (hasattr(m, 'speaker_id') and m.speaker_id == 'player') or (isinstance(m, dict) and m.get('speaker_id') == 'player') else npc_name}: {m.text if hasattr(m, 'text') else m.get('text', '')}"
        for m in dialogue_history[-4:]
    ])
    prompt = (
        f"当前对话：\n{history_text}\n\n"
        f"请为玩家生成2个不同的简短回应选项（每个不超过30字），"
        f"用竖线 | 分隔。注意：不要带编号、不要引号、不要'选项A'等前缀，"
        f"直接输出口语化的回应文本，像真实对话一样。"
    )
    response = client.chat(system_prompt, [{"role": "user", "content": prompt}])
    parts = response.split("|") if "|" in response else response.split("\n")
    # 清洗每个选项
    cleaned = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # 去掉各种编号前缀：A. 1. 选项A 选项1 (A) [A] 等
        p = re.sub(r'^[（(]\s*[A-Za-z0-9]\s*[）)]\s*', '', p)
        p = re.sub(r'^[（(]\s*[A-Za-z0-9]\s*[）)]\s*[:：]?\s*', '', p)
        p = re.sub(r'^选项\s*[A-Za-z0-9一二三四五六七八九十]\s*[:：]?\s*', '', p)
        p = re.sub(r'^[A-Za-z]\s*[.、．，,]\s*', '', p)
        p = re.sub(r'^\d+\s*[.、．，,]\s*', '', p)
        p = re.sub(r'^[""\'\'「」『』]\s*', '', p)
        p = re.sub(r'\s*[""\'\'「」『』]\s*$', '', p)
        p = p.strip()
        if p:
            cleaned.append(p[:40])
    suggestions = cleaned[:2]
    if len(suggestions) < 2:
        suggestions = (suggestions + ["让我再想想...", "请继续说。"])[:2]
    st.session_state[sugg_key] = suggestions


def _process_player_turn(state, branch_obj, ai_config, npc, system_prompt, text):
    """
    处理玩家一回合。
    返回 (action, state_or_none):
      - ("continue", new_state): 对话继续
      - ("rerun", None): 已设置 game_state 并调用 rerun（警告情况）
      - ("done", None): 已导航离开
    """
    loader = get_loader()
    chapter = loader.get_chapter(state.chapter_id)

    # 1. 添加玩家消息
    new_state = GameStateManager.add_dialogue(
        state, "player", "秦洛", text, is_ai=False
    )

    # 2. 检查负面关键词 → 警告但继续
    player_msgs = [m.text for m in new_state.dialogue_history if m.speaker_id == "player"]
    combined = " ".join(player_msgs)
    for cond in ai_config.failure_conditions:
        if cond.type == "semantic_match":
            if any(kw in combined for kw in cond.keywords_any):
                warn_state = GameStateManager.add_dialogue(
                    new_state, "system", "系统",
                    "（你的态度让对方感到不满。注意措辞，尝试更有建设性的方案。）",
                    is_ai=False,
                )
                st.session_state.game_state = warn_state
                st.rerun()
                return ("rerun", None)

    # 3. 调用 AI 生成 NPC 回复
    chat_history = [
        {"role": "user" if m.speaker_id == "player" else "assistant", "content": m.text}
        for m in new_state.dialogue_history
        if m.speaker_id != "system"
    ]
    client = AIClient()
    response = client.chat(system_prompt, chat_history)
    ai_state = GameStateManager.add_dialogue(
        new_state, ai_config.responding_character,
        npc.name_cn, response, is_ai=True
    )

    # 4. 检查成功关键词
    if _check_success_keywords(player_msgs, ai_config):
        _do_branch_success(ai_state, branch_obj, chapter)
        return ("done", None)

    # 5. 检查轮数 → 超限处理
    if ai_state.turn_count >= ai_config.max_turns:
        if ai_config.success_conditions:
            st.session_state.game_state = ai_state
            st.rerun()
            return ("rerun", None)
        else:
            final_state = GameStateManager.mark_branch_complete(
                ai_state, state.current_branch
            )
            st.session_state.game_state = GameStateManager.navigate_to_page(
                final_state, "P3"
            )
            st.rerun()
            return ("rerun", None)

    return ("continue", ai_state)


def _check_success_keywords(player_msgs: list[str], ai_config) -> bool:
    """检查玩家消息是否命中任一成功条件的关键词"""
    if not ai_config.success_conditions:
        return False
    combined = " ".join(player_msgs).lower()
    for cond in ai_config.success_conditions:
        if any(kw.lower() in combined for kw in cond.keywords_any):
            return True
    return False


def _do_branch_success(state, branch_obj, chapter):
    """标记分支成功并触发结局"""
    ending = None
    for e in chapter.endings:
        if e.trigger_branch == state.current_branch:
            ending = e
            break
    new_state = GameStateManager.mark_branch_complete(state, state.current_branch)
    if ending:
        new_state = GameStateManager.trigger_ending(new_state, ending.id)
    else:
        new_state = GameStateManager.navigate_to_page(new_state, "P3")
    st.session_state.game_state = new_state
    st.rerun()


def _handle_branch_failure(state, branch_obj, chapter, bg_b64):
    """分支失败 → 显示降级选项"""
    _scene_html(bg_b64, "", "对话陷入了僵局。或许可以换个方式表达？", speaker="系统")

    # 查找对应结局的 fallback 选项
    from engine.models import EndingType
    ending = None
    for e in chapter.endings:
        if e.trigger_branch == state.current_branch and e.type == EndingType.FAILURE:
            ending = e
            break
    if ending is None:
        for e in chapter.endings:
            if e.type == EndingType.FAILURE:
                ending = e
                break

    if ending and ending.fallback_options:
        st.caption("选择你的方案：")
        for opt in ending.fallback_options:
            def _select_fallback(branch=state.current_branch):
                new_state = GameStateManager.mark_branch_complete(state, branch)
                new_state = GameStateManager.trigger_ending(new_state, "ending_success")
                st.session_state.game_state = new_state
            st.button(opt.label, key=f"fb_{opt.id}",
                      on_click=_select_fallback, use_container_width=True)

    def _abandon():
        new_state = GameStateManager.mark_branch_complete(state, state.current_branch)
        st.session_state.game_state = GameStateManager.navigate_to_page(new_state, "P3")
    st.button("← 放弃此路线", key="give_up_branch",
              on_click=_abandon, use_container_width=True)


# ==================== 太阳风暴对话 ====================

def _render_solar_storm_dialogue(state, bg_b64, chapter):
    """太阳风暴过渡页：与柳夜的简短对话（旁白之后触发）— 统一交互模式"""
    loader = get_loader()
    liu_ye = loader.get_character("liu_ye")
    sprite_b64 = _img_b64(get_character_sprite("liu_ye"))

    # 初始化 session state
    storm_key = "solar_storm_dialogue"
    if storm_key not in st.session_state:
        st.session_state[storm_key] = {
            "history": [],
            "turn": 0,
            "started": False,
            "ended": False,
        }
    storm = st.session_state[storm_key]

    # 构建 system prompt（缓存）
    sys_key = "sys_solar_storm"
    if sys_key not in st.session_state:
        prompt_builder = PromptBuilder()
        st.session_state[sys_key] = prompt_builder.build(
            situation_prompt=(
                "太阳风暴刚刚爆发，辐射环境急剧恶化。两站所有人员的辐射暴露增加，"
                "药物需求急剧扩大。地球方面拒绝了紧急补给请求——运力优先分配给军事需求。"
                "柳叶（拓原站机械师，激进派，秦洛的朋友）对地球的回复感到愤怒。"
                "她认为这是抛弃，两站必须靠自己。现在她来和秦洛简短交谈。"
            ),
            responding_character_id="liu_ye",
            supporting_character_ids=[],
            chapter_id=state.chapter_id,
        )
    system_prompt = st.session_state[sys_key]

    # 开场白
    if not storm["started"]:
        storm["started"] = True
        client = AIClient()
        opening = client.chat(system_prompt, [
            {"role": "user", "content": "（太阳风暴刚爆发，地球拒绝了补给请求。你来和秦洛简短交谈，表达你的感受和想法。保持简短，2-3句话。）"}
        ])
        storm["history"].append({"role": "npc", "text": opening})
        # 生成 LLM 建议
        history = [{"speaker_id": "npc", "speaker_name": liu_ye.name_cn, "text": opening}]
        _gen_llm_suggestions("solar_storm", system_prompt, history, liu_ye.name_cn)
        st.rerun()

    # 已结束 → 推进到联合会议
    if storm["ended"]:
        new_state = GameStateManager.mark_node_complete(state, "transition_solar_storm")
        new_state = new_state.model_copy(update={
            "current_scene": "scene_joint_meeting",
            "current_beat_index": 0,
        })
        st.session_state.game_state = new_state
        st.session_state.pop(storm_key, None)
        if sys_key in st.session_state:
            st.session_state.pop(sys_key, None)
        sugg_key = "suggestions_solar_storm"
        if sugg_key in st.session_state:
            st.session_state.pop(sugg_key, None)
        st.rerun()

    # 显示对话状态
    st.caption("☀ 太阳风暴 · 与柳叶的对话")

    # 对话历史：第一条用背景，后续用纯对话框
    is_first_npc = True
    for msg in storm["history"]:
        if msg["role"] == "player":
            with st.container(border=True):
                st.caption("**秦洛（你）**")
                st.write(msg["text"])
        else:
            if is_first_npc:
                _scene_html(bg_b64, sprite_b64, msg["text"], speaker=liu_ye.name_cn)
                is_first_npc = False
            else:
                with st.container(border=True):
                    st.caption(f"**{liu_ye.name_cn}**")
                    st.write(msg["text"])

    # ---- 统一交互区 ----
    _render_unified_input("solar_storm", state, None, None,
                          liu_ye, system_prompt, chapter, bg_b64, sprite_b64,
                          is_branch=False)


def _storm_process_turn_inner(storm, system_prompt, npc, text):
    """处理太阳风暴对话的一个回合（不触发 rerun）"""
    storm["history"].append({"role": "player", "text": text})
    chat_history = [
        {"role": "user" if m["role"] == "player" else "assistant", "content": m["text"]}
        for m in storm["history"]
    ]
    client = AIClient()
    response = client.chat(system_prompt, chat_history)
    storm["history"].append({"role": "npc", "text": response})
    storm["turn"] += 1
    if storm["turn"] >= 5:
        storm["ended"] = True
