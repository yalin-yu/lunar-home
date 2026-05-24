"""素材路径管理"""

from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"

BACKGROUNDS = ASSETS_DIR / "backgrounds"
CHARACTERS = ASSETS_DIR / "characters"
UI = ASSETS_DIR / "ui"


def get_background(name: str) -> str:
    """返回背景图路径，不存在则返回 None"""
    path = BACKGROUNDS / name
    return str(path) if path.exists() else None


def get_character_sprite(char_id: str) -> str:
    """返回角色立绘路径"""
    # 角色ID到文件名映射
    sprite_map = {
        "qin_luo": "qin_luo.png",
        "wolff": "person_1.png",
        "kovali": "person_2.png",
        "lind": "person_1.png",
        "fang_henian": "person_1.png",
        "liu_ye": "person_2.png",
        "neumann": "person_2.png",
        "xu_heng": "person_2.png",
    }
    filename = sprite_map.get(char_id, "default.png")
    path = CHARACTERS / filename
    return str(path) if path.exists() else None


def get_ui_asset(name: str) -> str:
    """返回 UI 素材路径"""
    path = UI / name
    return str(path) if path.exists() else None


# 场景到背景图的映射
SCENE_BACKGROUND_MAP = {
    "scene_opening": "lunar_base.png",
    "scene_medical_bay": "default.png",
    "scene_command_hall": "lunar_base2.png",
    "transition_solar_storm": "lunar_base.png",
    "scene_joint_meeting": "lunar_base2.png",
    "scene_epilogue": "lunar_base.png",
    "ending_success": "lunar_base.png",
    "ending_failure": "default.png",
}


def get_scene_background(scene_id: str) -> str:
    filename = SCENE_BACKGROUND_MAP.get(scene_id, "default.png")
    path = BACKGROUNDS / filename
    return str(path) if path.exists() else None
