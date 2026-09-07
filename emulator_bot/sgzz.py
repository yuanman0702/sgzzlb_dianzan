from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import sleep, time
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
import cv2
import numpy as np

from .bot import EmulatorBot
from .vision import Match, match_template


DEFAULT_SGZZ_CLIENT = "灵犀"
SGZZ_CLIENT_PACKAGES: dict[str, str] = {
    "灵犀": "com.aligames.sgzzlb",
    "小米": "com.aligames.sgzzlb.mi",
    "九游": "com.uc.game.sgzzlb",
    "华为": "com.aligames.sgzzlb.huawei",
    "QQ": "com.tencent.tmgp.s3.sgzzlb",
}
SGZZ_CLIENT_TYPES: tuple[str, ...] = tuple(SGZZ_CLIENT_PACKAGES)
SGZZ_PACKAGE = SGZZ_CLIENT_PACKAGES[DEFAULT_SGZZ_CLIENT]
OVERLAY_BRIDGE_PACKAGE = "com.example.overlaybridge"
TEMPLATE_PREFIX = "sgzz"
DEFAULT_SGZZ_ACCOUNTS_FILE = Path(__file__).resolve().parents[1] / "sgzz_accounts.txt"
DEFAULT_SGZZ_LIKE_TARGET_FILE = Path(__file__).resolve().parents[1] / "sgzz_like_target.txt"
SGZZ_LIKE_TARGET_ENV = "SGZZ_LIKE_TARGET_QUERY_ID"
TEMPLATES = {
    "title_select_server": f"{TEMPLATE_PREFIX}/title_select_server.png",
    "title_enter_button": f"{TEMPLATE_PREFIX}/title_enter_button.png",
    "title_return_login_button": f"{TEMPLATE_PREFIX}/title_return_login_button.png",
    "restore_cancel_button": f"{TEMPLATE_PREFIX}/restore_cancel_button.png",
    "server_selector_title": f"{TEMPLATE_PREFIX}/server_selector_title.png",
    "season1_tab": f"{TEMPLATE_PREFIX}/season1_tab.png",
    "queue_title": f"{TEMPLATE_PREFIX}/queue_title.png",
    "dialog_continue_icon": f"{TEMPLATE_PREFIX}/dialog_continue_icon.png",
    "old_man_marker": f"{TEMPLATE_PREFIX}/old_man_marker.png",
    "avatar_confirm_button": f"{TEMPLATE_PREFIX}/avatar_confirm_button.png",
    "name_enter_button": f"{TEMPLATE_PREFIX}/name_enter_button.png",
    "region_select_title": f"{TEMPLATE_PREFIX}/region_select_title.png",
    "xiliang_enter_button": f"{TEMPLATE_PREFIX}/xiliang_enter_button.png",
    "chapter_next_button": f"{TEMPLATE_PREFIX}/chapter_next_button.png",
    "scout_marker": f"{TEMPLATE_PREFIX}/scout_marker.png",
    "zhuge_marker": f"{TEMPLATE_PREFIX}/zhuge_marker.png",
    "landscape_dialog_continue_icon": f"{TEMPLATE_PREFIX}/landscape_dialog_continue_icon.png",
    "tongpao_feature_marker": f"{TEMPLATE_PREFIX}/tongpao_feature_marker.png",
    "alliance_button": f"{TEMPLATE_PREFIX}/alliance_button.png",
    "signin_reward_title": f"{TEMPLATE_PREFIX}/signin_reward_title_x2.png",
    "signin_reward_title_small": f"{TEMPLATE_PREFIX}/signin_reward_title.png",
    "signin_reward_confirm_button": f"{TEMPLATE_PREFIX}/signin_reward_confirm_button_x2.png",
    "signin_reward_confirm_button_small": f"{TEMPLATE_PREFIX}/signin_reward_confirm_button.png",
    "orange_card_down_arrow": f"{TEMPLATE_PREFIX}/orange_card_down_arrow.png",
    "gacha_orange_card_down_arrow": f"{TEMPLATE_PREFIX}/gacha_orange_card_down_arrow.png",
    "click_other_area_return_hint": f"{TEMPLATE_PREFIX}/click_other_area_return_hint.png",
    "click_other_area_return_hint_x2": f"{TEMPLATE_PREFIX}/click_other_area_return_hint_x2.png",
    "click_other_area_return_hint_game": f"{TEMPLATE_PREFIX}/click_other_area_return_hint_game.png",
    "click_other_area_return_hint_game_x2": f"{TEMPLATE_PREFIX}/click_other_area_return_hint_game_x2.png",
    "alliance_back_button": f"{TEMPLATE_PREFIX}/alliance_back_button.png",
    "alliance_back_button_x2": f"{TEMPLATE_PREFIX}/alliance_back_button_x2.png",
    "main_recruit_button": f"{TEMPLATE_PREFIX}/main_recruit_button.png",
    "main_friend_button": f"{TEMPLATE_PREFIX}/main_friend_button.png",
    "like_dabai_friend_card": f"{TEMPLATE_PREFIX}/like_dabai_friend_card.png",
    "like_dabai_friend_button": f"{TEMPLATE_PREFIX}/like_dabai_friend_button.png",
    "like_friend_search_icon": f"{TEMPLATE_PREFIX}/like_friend_search_icon.png",
    "like_friend_query_title": f"{TEMPLATE_PREFIX}/like_friend_query_title.png",
    "like_friend_search_button": f"{TEMPLATE_PREFIX}/like_friend_search_button.png",
    "like_friend_search_result_dabai": f"{TEMPLATE_PREFIX}/like_friend_search_result_dabai.png",
    "like_friend_add_button": f"{TEMPLATE_PREFIX}/like_friend_add_button.png",
    "like_friend_add_pending_button": f"{TEMPLATE_PREFIX}/like_friend_add_pending_button.png",
    "like_friend_request_sent_toast": f"{TEMPLATE_PREFIX}/like_friend_request_sent_toast.png",
    "like_personal_info_button": f"{TEMPLATE_PREFIX}/like_personal_info_button.png",
    "like_personal_home_view_button": f"{TEMPLATE_PREFIX}/like_personal_home_view_button.png",
    "like_home_like_button": f"{TEMPLATE_PREFIX}/like_home_like_button.png",
    "like_limit_toast_text": f"{TEMPLATE_PREFIX}/like_limit_toast_text.png",
    "like_home_back_button": f"{TEMPLATE_PREFIX}/like_home_back_button.png",
    "like_friends_back_button": f"{TEMPLATE_PREFIX}/like_friends_back_button.png",
    "gacha_named_pack_tab": f"{TEMPLATE_PREFIX}/gacha_named_pack_tab.png",
    "gacha_recruit_once_button": f"{TEMPLATE_PREFIX}/gacha_recruit_once_button.png",
    "gacha_recruit_once_free_badge": f"{TEMPLATE_PREFIX}/gacha_recruit_once_free_badge.png",
    "gacha_recruit_once_half_button": f"{TEMPLATE_PREFIX}/gacha_recruit_once_half_button.png",
    "gacha_recruit_once_half_badge": f"{TEMPLATE_PREFIX}/gacha_recruit_once_half_badge.png",
    "gacha_result_back_button": f"{TEMPLATE_PREFIX}/gacha_result_back_button.png",
    "gacha_recruit_page_back_button": f"{TEMPLATE_PREFIX}/gacha_recruit_page_back_button.png",
    "main_social_button": f"{TEMPLATE_PREFIX}/main_social_button.png",
    "gamecircle_signin_welfare_button": f"{TEMPLATE_PREFIX}/gamecircle_signin_welfare_button.png",
    "gamecircle_pending_claim_label": f"{TEMPLATE_PREFIX}/gamecircle_pending_claim_label.png",
    "gamecircle_signin_success_confirm_button": f"{TEMPLATE_PREFIX}/gamecircle_signin_success_confirm_button.png",
    "gamecircle_exit_button": f"{TEMPLATE_PREFIX}/gamecircle_exit_button.png",
    "account_more_button": f"{TEMPLATE_PREFIX}/account_more_button.png",
    "account_system_button": f"{TEMPLATE_PREFIX}/account_system_button.png",
    "account_system_settings_title": f"{TEMPLATE_PREFIX}/account_system_settings_title.png",
    "account_switch_account_button": f"{TEMPLATE_PREFIX}/account_switch_account_button.png",
    "account_login_modal_logo": f"{TEMPLATE_PREFIX}/account_login_modal_logo.png",
    "account_login_button": f"{TEMPLATE_PREFIX}/account_login_button.png",
    "xiaomi_quick_login_decline_button": f"{TEMPLATE_PREFIX}/xiaomi_quick_login_decline_button.png",
    "xiaomi_graphics_settings_save_button": f"{TEMPLATE_PREFIX}/xiaomi_graphics_settings_save_button.png",
    "xiaomi_missing_resources_confirm_button": f"{TEMPLATE_PREFIX}/xiaomi_missing_resources_confirm_button.png",
    "xiaomi_background_resources_confirm_button": f"{TEMPLATE_PREFIX}/xiaomi_background_resources_confirm_button.png",
    "enter_world_again_button": f"{TEMPLATE_PREFIX}/enter_world_again_button.png",
    "role_enter_battle_button": f"{TEMPLATE_PREFIX}/role_enter_battle_button.png",
    "region_select_title_top": f"{TEMPLATE_PREFIX}/region_select_title_top.png",
    "region_enter_label": f"{TEMPLATE_PREFIX}/region_enter_label.png",
    "region_enter_selected_button": f"{TEMPLATE_PREFIX}/region_enter_selected_button.png",
    "region_confirm_label": f"{TEMPLATE_PREFIX}/region_confirm_label.png",
    "region_confirm_button": f"{TEMPLATE_PREFIX}/region_confirm_button.png",
    "military_council_title": f"{TEMPLATE_PREFIX}/military_council_title.png",
    "military_council_back_button": f"{TEMPLATE_PREFIX}/military_council_back_button.png",
    "main_known_retreat_button": f"{TEMPLATE_PREFIX}/main_known_retreat_button.png",
    "exit_confirm_title": f"{TEMPLATE_PREFIX}/exit_confirm_title.png",
    "exit_stay_button": f"{TEMPLATE_PREFIX}/exit_stay_button.png",
    "inactive_reselect_prompt_title": f"{TEMPLATE_PREFIX}/inactive_reselect_prompt_title.png",
    "inactive_reselect_confirm_button": f"{TEMPLATE_PREFIX}/inactive_reselect_confirm_button.png",
}


@dataclass(frozen=True, repr=False)
class SGZZAccountCredential:
    account: str
    password: str
    line_number: int
    client: str = DEFAULT_SGZZ_CLIENT

    @property
    def masked_account(self) -> str:
        return mask_sgzz_account(self.account)

    @property
    def account_key(self) -> str:
        return sgzz_account_key(self.account, self.client)

    @property
    def package(self) -> str:
        return SGZZ_CLIENT_PACKAGES[self.client]


def sgzz_account_key(account: str, client: str | None = None) -> str:
    text = str(account).strip()
    normalized_client = normalize_sgzz_client(client)
    # Keep existing Lingxi keys stable so today's completion state survives the migration.
    identity = text if normalized_client == DEFAULT_SGZZ_CLIENT else f"{normalized_client}\0{text}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]


def mask_sgzz_account(account: str) -> str:
    text = str(account).strip()
    if len(text) <= 4:
        return "*" * len(text)
    if len(text) <= 7:
        return f"{text[:2]}***{text[-2:]}"
    return f"{text[:3]}***{text[-4:]}"


def normalize_sgzz_client(client: str | None) -> str:
    value = str(client or "").strip()
    if not value:
        return DEFAULT_SGZZ_CLIENT
    aliases = {
        "lingxi": "灵犀",
        "官方": "灵犀",
        "官服": "灵犀",
        "xiaomi": "小米",
        "mi": "小米",
        "uc": "九游",
        "9game": "九游",
        "huawei": "华为",
        "qq": "QQ",
        "腾讯": "QQ",
        "应用宝": "QQ",
    }
    normalized = aliases.get(value.lower(), value)
    if normalized not in SGZZ_CLIENT_PACKAGES:
        choices = "、".join(SGZZ_CLIENT_TYPES)
        raise ValueError(f"Unsupported SGZZ client: {value}. Expected one of: {choices}.")
    return normalized


def parse_sgzz_account_credentials_text(text: str) -> list[SGZZAccountCredential]:
    credentials: list[SGZZAccountCredential] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("#")]
        if len(parts) not in {2, 3}:
            raise ValueError(
                f"Invalid SGZZ account config at line {line_number}: "
                "expected account#password or account#password#client."
            )
        account, password = parts[:2]
        if not account or not password:
            raise ValueError(
                f"Invalid SGZZ account config at line {line_number}: account and password are required."
            )
        client = normalize_sgzz_client(parts[2] if len(parts) == 3 else None)
        credentials.append(
            SGZZAccountCredential(
                account=account,
                password=password,
                line_number=line_number,
                client=client,
            )
        )
    if not credentials:
        raise ValueError("SGZZ account config has no usable accounts.")
    return credentials


def serialize_sgzz_account_credential(credential: SGZZAccountCredential) -> str:
    return f"{credential.account}#{credential.password}#{credential.client}"


def resolve_sgzz_like_target_query_id(value: str | None = None) -> str:
    candidates = [value, os.environ.get(SGZZ_LIKE_TARGET_ENV)]
    for candidate in candidates:
        text = str(candidate or "").strip()
        if text:
            return text
    if DEFAULT_SGZZ_LIKE_TARGET_FILE.exists():
        for line in DEFAULT_SGZZ_LIKE_TARGET_FILE.read_text(encoding="utf-8-sig").splitlines():
            text = line.strip()
            if text and not text.startswith("#"):
                return text
    raise RuntimeError(
        "Missing SGZZ like target player ID. Set SGZZ_LIKE_TARGET_QUERY_ID "
        "or create sgzz_like_target.txt."
    )


def resolve_sgzz_accounts_file(path: str | Path | None = None) -> Path:
    if path is None:
        env_path = os.environ.get("SGZZ_ACCOUNTS_FILE", "").strip()
        path = env_path or DEFAULT_SGZZ_ACCOUNTS_FILE
    out = Path(path)
    if not out.is_absolute():
        out = DEFAULT_SGZZ_ACCOUNTS_FILE.parent / out
    return out


def load_sgzz_account_credentials(path: str | Path | None = None) -> list[SGZZAccountCredential]:
    account_path = resolve_sgzz_accounts_file(path)
    if not account_path.exists():
        raise FileNotFoundError(f"SGZZ account config file not found: {account_path}")

    try:
        return parse_sgzz_account_credentials_text(account_path.read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        if "has no usable accounts" in str(exc):
            raise ValueError(f"SGZZ account config has no usable accounts: {account_path}") from exc
        raise


SGZZ_FLOW_NODES: tuple[dict[str, str], ...] = (
    {
        "node": "select_latest_s1",
        "detect": "标题页/选服弹窗/赛季1标签",
        "action": "启动游戏，进入普通赛季1最新服，点前往征战",
    },
    {
        "node": "select_last_server_entry",
        "detect": "选服列表",
        "action": "点击选服，列表下滑到最底，点最后一个角色",
    },
    {
        "node": "select_last_server_role_only",
        "detect": "选服列表头像列",
        "action": "点击选服，列表下滑到最底，只选中最后一个角色，不确认进入",
    },
    {
        "node": "confirm_selected_server_entry",
        "detect": "选服弹窗/标题页前往征战",
        "action": "点击选服弹窗确定按钮，再点前往征战进入游戏",
    },
    {
        "node": "tongpao_feature_prompt",
        "detect": "同袍功能引导标识/底部同盟按钮",
        "action": "检测到同袍功能标识后，点击底部同盟按钮，关闭点赞前置引导",
    },
    {
        "node": "signin_reward_prompt",
        "detect": "今日签到奖励弹窗",
        "action": "检测签到奖励弹窗，点击确定关闭",
    },
    {
        "node": "enter_world_again_prompt",
        "detect": "横屏再争乱世入口",
        "action": "检测到再争乱世按钮后点击，继续进入游戏主界面",
    },
    {
        "node": "same_server_select_last_role",
        "detect": "同区多角色选择页",
        "action": "检测到同一服务器内多个角色时，选择最右侧/最后一个角色",
    },
    {
        "node": "region_default_select_prompt",
        "detect": "选择起兵之地",
        "action": "检测到选州/起兵之地页面后，点击当前默认推荐入驻按钮",
    },
    {
        "node": "inactive_reselect_region_prompt",
        "detect": "长期非活跃重新选择起兵之地提示",
        "action": "检测到老角色重新选州提示后，点击确定进入默认选州流程",
    },
    {
        "node": "military_council_back_prompt",
        "detect": "军议页面",
        "action": "检测到军议前置页后，点击左下返回回到主界面",
    },
    {
        "node": "exit_confirm_prompt",
        "detect": "退出确认弹窗",
        "action": "检测到退出确认后点击再玩一会，避免主界面返回误退出游戏",
    },
    {
        "node": "recover_to_main_screen",
        "detect": "任意误入页面/左下返回按钮/主界面绿色招募按钮",
        "action": "异常矫正：不在流程页面时连续点返回，直到回到带招募按钮的主界面",
    },
    {
        "node": "orange_card_effect_prompt",
        "detect": "橙卡特效右下角动态向下箭头",
        "action": "循环识别动态向下箭头并点击，跳过橙卡特效",
    },
    {
        "node": "click_other_area_return_hint",
        "detect": "底部点击其他区域返回提示",
        "action": "检测到底部点击其他区域返回标识后点击，返回上一层",
    },
    {
        "node": "alliance_back_to_main",
        "detect": "同盟页左下角返回按钮",
        "action": "点击同盟页返回按钮，回到游戏主界面",
    },
    {
        "node": "like_open_friends_list",
        "detect": "主界面右下角绿色招募按钮/左侧好友按钮",
        "action": "点赞流程：确认主界面后打开左侧好友列表",
    },
    {
        "node": "like_click_dabai_friend_button",
        "detect": "好友列表/大白丨二大大好友卡片",
        "action": "点赞流程：定位大白丨二大大好友卡片，点击头像旁小按钮",
    },
    {
        "node": "like_add_missing_dabai_friend",
        "detect": "好友列表中未找到大白丨二大大/查询添加弹窗",
        "action": "点赞流程：按本地配置的目标编号查询并发送好友申请，然后正常返回",
    },
    {
        "node": "like_click_personal_info_button",
        "detect": "玩家操作弹层/个人信息按钮",
        "action": "点赞流程：点击个人信息按钮，进入玩家个人信息页",
    },
    {
        "node": "like_click_personal_home_view_button",
        "detect": "个人详情页/个人主页点击查看按钮",
        "action": "点赞流程：点击个人主页的点击查看按钮",
    },
    {
        "node": "like_click_home_like_button",
        "detect": "个人主页/右下角点赞按钮",
        "action": "点赞流程：连续点击右下角点赞按钮5次",
    },
    {
        "node": "like_click_home_back_button",
        "detect": "个人主页/左下角返回按钮",
        "action": "点赞流程：点击左下角返回按钮",
    },
    {
        "node": "like_click_friends_back_button",
        "detect": "好友列表/左下角返回按钮",
        "action": "点赞流程：从好友列表点击左下角返回按钮",
    },
    {
        "node": "gacha_open_recruit_if_red_dot",
        "detect": "主界面右下角招募按钮/招募按钮小红点",
        "action": "抽卡流程：检测招募按钮小红点，有红点才点击招募",
    },
    {
        "node": "gacha_select_named_pack",
        "detect": "招募页底部名将卡包",
        "action": "抽卡流程：连续左滑查找名将卡包，找到后点击",
    },
    {
        "node": "gacha_click_free_recruit_once",
        "detect": "名将卡包/招募1次按钮/免费角标",
        "action": "抽卡流程：确认招募1次按钮右上角有免费字样后点击一次",
    },
    {
        "node": "gacha_click_half_recruit_once",
        "detect": "名将卡包/招募1次按钮/半价角标",
        "action": "抽卡流程：确认招募1次按钮右上角有半价标识后点击一次",
    },
    {
        "node": "gacha_back_from_recruit_result",
        "detect": "抽卡结果页/橙卡特效/左下角返回按钮",
        "action": "抽卡流程：先尝试处理橙卡特效，再点击左下角返回按钮",
    },
    {
        "node": "gacha_back_from_recruit_page",
        "detect": "招募页/左下角返回按钮",
        "action": "抽卡流程：从招募页点击左下角返回按钮回到主界面",
    },
    {
        "node": "gacha_free_and_half",
        "detect": "主界面招募红点/免费角标/半价角标/抽卡结果页",
        "action": "抽卡流程：依次完成免费和半价招募，处理橙卡后返回主界面",
    },
    {
        "node": "gamecircle_signin",
        "detect": "主界面社按钮/游戏圈签到福利/待签到标签",
        "action": "游戏圈签到：点击社、签到福利、待签到标签，确认奖励后退出",
    },
    {
        "node": "account_switch_to_role_select",
        "detect": "主界面更多按钮/系统按钮/切换账号按钮",
        "action": "切换账号流程：更多->系统->切换账号，回到切换角色流程",
    },
    {
        "node": "account_login_and_select_last_role",
        "detect": "登录弹窗/标题页点击选服/选服列表头像列",
        "action": "切换账号流程：当前账号登录后进入选服，下拉选择最后一个角色并确定进入",
    },
    {
        "node": "daily_signin_like_gacha",
        "detect": "签到奖励/同袍引导/好友列表/招募红点/免费角标/半价角标/游戏圈签到福利",
        "action": "点赞流程：处理签到后执行点赞5次，可选免费和半价抽卡、游戏圈签到",
    },
    {
        "node": "account_role_daily_cycle",
        "detect": "主界面/登录页/选服列表/日常流程",
        "action": "循环流程：切换账号->登录当前账号->选择最后一个角色->执行签到、点赞和可选抽卡",
    },
    {
        "node": "account_remaining_roles_daily_cycle",
        "detect": "主界面/登录页/选服列表/最后一行角色图像指纹",
        "action": "从当前已完成角色继续，循环处理本账号剩余角色，直到选服列表最后一行重复",
    },
    {
        "node": "account_batch_remaining_roles_daily_cycle",
        "detect": "账号配置文件/登录弹窗/角色区服身份截图",
        "action": "点赞全流程：按账号配置逐个登录，跑完每个账号所有角色后切下一个，全部跑完停止",
    },
    {
        "node": "main_known_retreat_prompt",
        "detect": "主界面引导浮层/已知退下按钮",
        "action": "异常处理：检测到已知退下按钮后点击关闭",
    },
    {
        "node": "old_man_intro",
        "detect": "old_man_marker.png",
        "action": "老者在场时连续点继续，问答默认点顶部选项",
    },
    {
        "node": "create_character_xiliang",
        "detect": "头像确认/进入乱世/落州页",
        "action": "确认头像，提交随机名，落州选择西凉",
    },
    {
        "node": "opening_dialogs",
        "detect": "scout_marker.png / zhuge_marker.png",
        "action": "斥候、诸葛亮在场时连续点右下继续",
    },
    {
        "node": "recruit_free_twice",
        "detect": "招募按钮/免费招募按钮",
        "action": "打开招募，点招募2次免费，关闭结果页返回地图",
    },
    {
        "node": "initial_team_config",
        "detect": "城内部队一/部队配置页",
        "action": "曹休主将、孙乾副将、快速分兵，返回地图",
    },
    {
        "node": "first_occupy",
        "detect": "教程高亮的第一块地",
        "action": "点目标地，攻占，选择曹休队，确认出征，领取首占奖励",
    },
    {
        "node": "spear_config",
        "detect": "选择主城/部队配置页/兵种选择",
        "action": "进城进入部队配置，切枪兵，确认分兵，返回地图",
    },
    {
        "node": "support_ally",
        "detect": "选择目标领地，支援义军",
        "action": "点高亮义军地，行军，选择曹休队，确认，战斗跳过，回城",
    },
    {
        "node": "reassign_main_after_support",
        "detect": "部队配置页提示下阵曹休",
        "action": "下阵曹休，确认，再点主将位上阵关平",
    },
    {
        "node": "open_recruit_from_map",
        "detect": "主地图底部招募按钮",
        "action": "从地图进入招募页",
    },
    {
        "node": "recruit_named_once",
        "detect": "招募页底部名将卡包",
        "action": "确认名将卡包，点招募1次免费，记录新武将",
    },
    {
        "node": "configure_second_team",
        "detect": "主城界面部队二/部队配置页",
        "action": "第二队放入新招募武将和主公武将，补满兵",
    },
    {
        "node": "probe_land",
        "detect": "地图土地面板",
        "action": "点候选土地，仅截图记录等级和是否可攻占，不确认出征",
    },
    {
        "node": "farm_land",
        "detect": "地图土地面板/出征确认页",
        "action": "空地用一队铺路，1/2/3级地用二队攻占",
    },
)


@dataclass(frozen=True, slots=True)
class Point:
    x: int
    y: int


class SGZZScreenStuckRestart(RuntimeError):
    """Raised after the watchdog restarts the game so the flow can retry."""


class SGZZStopRequested(RuntimeError):
    """Raised when the controller requests the active SGZZ job to stop."""


@dataclass(frozen=True, slots=True)
class SGZZCoordinates:
    restore_cancel: Point = Point(464, 754)
    title_select_server: Point = Point(486, 920)
    season1_tab: Point = Point(318, 1036)
    latest_s1_server: Point = Point(185, 219)
    server_confirm: Point = Point(360, 1118)
    server_hidden_roles_toggle: Point = Point(580, 1118)
    title_enter: Point = Point(360, 1004)
    dialog_continue: Point = Point(674, 904)
    old_man_choice_top: Point = Point(535, 554)
    old_man_choice_middle: Point = Point(535, 641)
    old_man_choice_bottom: Point = Point(535, 727)
    avatar_confirm: Point = Point(360, 1146)
    name_enter_world: Point = Point(360, 1146)
    xiliang_region: Point = Point(160, 330)
    xiliang_enter: Point = Point(360, 1210)
    region_popup_confirm: Point = Point(254, 754)
    chapter_next: Point = Point(1190, 681)
    landscape_dialog_continue: Point = Point(1158, 568)
    resource_prompt_confirm: Point = Point(270, 754)
    main_city_center: Point = Point(640, 360)
    main_city_enter: Point = Point(640, 333)
    server_selector_swipe_start: Point = Point(360, 980)
    server_selector_swipe_end: Point = Point(360, 420)
    server_selector_last_entry: Point = Point(360, 1110)
    city_back: Point = Point(1190, 31)
    map_back: Point = Point(1238, 31)
    troop_one_card: Point = Point(125, 640)
    troop_compile: Point = Point(210, 682)
    main_general_plus: Point = Point(424, 253)
    deputy_general_plus: Point = Point(640, 258)
    general_list_first_up: Point = Point(1233, 229)
    general_list_second_up: Point = Point(1233, 306)
    quick_conscription: Point = Point(146, 687)
    conscription_confirm: Point = Point(1124, 592)
    troop_type_button: Point = Point(1160, 416)
    spear_type: Point = Point(1000, 343)
    split_confirm: Point = Point(1135, 585)
    recruit_button: Point = Point(920, 667)
    recruit_twice_free: Point = Point(790, 571)
    recruit_result_continue: Point = Point(1030, 650)
    first_land_target: Point = Point(644, 331)
    support_land_target: Point = Point(646, 335)
    occupy_button: Point = Point(880, 181)
    march_button: Point = Point(880, 244)
    troop_card: Point = Point(640, 635)
    march_confirm: Point = Point(997, 495)
    battle_skip: Point = Point(85, 688)
    first_reward: Point = Point(640, 350)
    recall_button: Point = Point(1196, 239)
    caoxiu_dismiss: Point = Point(490, 100)
    popup_confirm: Point = Point(535, 474)
    portrait_back: Point = Point(105, 1242)
    portrait_map_recruit: Point = Point(650, 1218)
    portrait_named_pack: Point = Point(293, 1020)
    portrait_named_recruit_once: Point = Point(217, 835)
    portrait_recruit_result_continue: Point = Point(360, 1120)
    portrait_close_land_panel: Point = Point(690, 1020)
    portrait_alliance_button: Point = Point(197, 1144)
    portrait_friend_button: Point = Point(82, 1014)
    portrait_main_recruit_button: Point = Point(650, 1202)
    portrait_land_occupy: Point = Point(598, 729)
    portrait_land_march: Point = Point(598, 791)
    portrait_second_team_card: Point = Point(218, 1073)
    portrait_main_general_plus: Point = Point(144, 609)
    portrait_deputy_general_plus: Point = Point(361, 609)
    portrait_general_first_up: Point = Point(613, 676)
    portrait_general_second_up: Point = Point(613, 772)
    portrait_quick_conscription: Point = Point(103, 1030)
    portrait_split_confirm: Point = Point(361, 1130)
    portrait_main_city: Point = Point(360, 680)
    portrait_main_city_enter: Point = Point(360, 610)


class SGZZStartAccountRunner:
    """Small stateful runner for the S1-new-server entry path."""

    def __init__(
        self,
        bot: EmulatorBot,
        *,
        package: str = SGZZ_PACKAGE,
        run_dir: Path | None = None,
        coords: SGZZCoordinates | None = None,
        quick_delay_seconds: float = 0.12,
        stop_requested: Callable[[], bool] | None = None,
    ) -> None:
        self.bot = bot
        self.package = package
        self.client_name = next(
            (name for name, package_name in SGZZ_CLIENT_PACKAGES.items() if package_name == package),
            DEFAULT_SGZZ_CLIENT,
        )
        self.coords = coords or SGZZCoordinates()
        self.quick_delay_seconds = quick_delay_seconds
        self.stop_requested = stop_requested
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = run_dir or bot.config.screenshot_dir.parent / "sgzz_runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.record_path = self.run_dir / "steps.jsonl"
        self._step_index = 0
        self._xiaomi_login_ui_state: str | None = None
        self._watchdog_enabled = os.environ.get("SGZZ_STUCK_WATCHDOG", "1").lower() not in {
            "0",
            "false",
            "off",
            "no",
        }
        self._watchdog_timeout_seconds = float(os.environ.get("SGZZ_STUCK_SECONDS", "30"))
        self._black_screen_timeout_seconds = float(os.environ.get("SGZZ_BLACK_SCREEN_SECONDS", "30"))
        self._black_screen_dark_threshold = int(os.environ.get("SGZZ_BLACK_SCREEN_DARK_THRESHOLD", "18"))
        self._black_screen_dark_ratio = float(os.environ.get("SGZZ_BLACK_SCREEN_DARK_RATIO", "0.985"))
        self._black_screen_mean_threshold = float(os.environ.get("SGZZ_BLACK_SCREEN_MEAN", "12"))
        self._black_screen_edge_ratio = float(os.environ.get("SGZZ_BLACK_SCREEN_EDGE_RATIO", "0.003"))
        self._black_screen_started_at = 0.0
        self._black_screen_last_record_at = 0.0
        self._screenshot_format = os.environ.get("SGZZ_SCREENSHOT_FORMAT", "jpg").strip().lower()
        if self._screenshot_format not in {"jpg", "jpeg", "png"}:
            self._screenshot_format = "jpg"
        self._screenshot_jpeg_quality = max(
            1,
            min(100, int(os.environ.get("SGZZ_SCREENSHOT_JPEG_QUALITY", "70"))),
        )
        self._run_log_cleanup_enabled = os.environ.get(
            "SGZZ_RUN_LOG_CLEANUP",
            "1",
        ).lower() not in {"0", "false", "off", "no"}
        self._run_log_cleanup_interval_seconds = float(
            os.environ.get("SGZZ_RUN_LOG_CLEANUP_INTERVAL_SECONDS", "30")
        )
        self._run_log_keep_images = max(20, int(os.environ.get("SGZZ_RUN_LOG_KEEP_IMAGES", "180")))
        self._run_log_min_recent_images = max(
            10,
            int(os.environ.get("SGZZ_RUN_LOG_MIN_RECENT_IMAGES", "30")),
        )
        self._run_log_max_bytes = max(
            50 * 1024 * 1024,
            int(float(os.environ.get("SGZZ_RUN_LOG_MAX_MB", "300")) * 1024 * 1024),
        )
        self._run_log_last_cleanup_at = 0.0
        self._watchdog_sample_interval_seconds = float(
            os.environ.get("SGZZ_STUCK_SAMPLE_INTERVAL", "3")
        )
        self._watchdog_min_static_regions = int(os.environ.get("SGZZ_STUCK_MIN_STATIC_REGIONS", "3"))
        self._watchdog_diff_threshold = float(os.environ.get("SGZZ_STUCK_REGION_DIFF_THRESHOLD", "1.0"))
        self._watchdog_progress_diff_threshold = float(
            os.environ.get("SGZZ_STUCK_PROGRESS_REGION_DIFF", "4.0")
        )
        self._watchdog_whole_progress_diff_threshold = float(
            os.environ.get("SGZZ_STUCK_WHOLE_PROGRESS_DIFF", "2.0")
        )
        self._watchdog_restart_limit = int(os.environ.get("SGZZ_STUCK_RESTART_LIMIT", "8"))
        self._watchdog_last_sample_at = 0.0
        self._watchdog_anchor_at = 0.0
        self._watchdog_anchor: dict[str, np.ndarray] | None = None
        self._watchdog_restarting = False
        self._watchdog_restarts = 0
        self._foreground_last_check_at = 0.0
        self._foreground_check_interval_seconds = float(
            os.environ.get("SGZZ_FOREGROUND_CHECK_INTERVAL", "2.0")
        )
        self.fast_mode = os.environ.get("SGZZ_FAST_MODE", "1").lower() not in {
            "0",
            "false",
            "off",
            "no",
        }
        self.main_template_timeout_seconds = float(
            os.environ.get("SGZZ_MAIN_TEMPLATE_TIMEOUT", "0.25" if self.fast_mode else "0.8")
        )
        self.optional_prompt_timeout_seconds = float(
            os.environ.get("SGZZ_OPTIONAL_PROMPT_TIMEOUT", "0.30" if self.fast_mode else "1.0")
        )
        self._last_like_limit_reached = False
        self._last_daily_like_done = False
        self._last_account_cycle_summary: dict[str, object] = {}

    def _check_stop_requested(self) -> None:
        if self.stop_requested is not None and self.stop_requested():
            self._record({"type": "state", "state": "stop_requested"})
            raise SGZZStopRequested("SGZZ job stop requested.")

    def _fast_timeout(self, normal_seconds: float, fast_seconds: float) -> float:
        return fast_seconds if self.fast_mode else normal_seconds

    def _fast_wait(self, normal_seconds: float, fast_seconds: float) -> float:
        return fast_seconds if self.fast_mode else normal_seconds

    def _record(self, event: dict[str, object]) -> None:
        payload = {"ts": datetime.now().isoformat(timespec="seconds"), **event}
        with self.record_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _snapshot_path(self, label: str) -> Path:
        extension = "png" if self._screenshot_format == "png" else "jpg"
        return self.run_dir / f"{self.run_id}_{self._step_index:03d}_{label}.{extension}"

    def _write_snapshot_image(self, path: Path, image: np.ndarray) -> None:
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            cv2.imwrite(
                str(path),
                image,
                [int(cv2.IMWRITE_JPEG_QUALITY), self._screenshot_jpeg_quality],
            )
            return
        cv2.imwrite(str(path), image)

    def _save_image_snapshot(self, label: str, image: np.ndarray) -> Path:
        self._step_index += 1
        path = self._snapshot_path(label)
        self._write_snapshot_image(path, image)
        self._record({"type": "screenshot", "label": label, "path": str(path)})
        self._maybe_cleanup_current_run_logs()
        return path

    @staticmethod
    def _is_protected_run_image(path: Path) -> bool:
        name = path.name.lower()
        return "account_role_identity_" in name

    def _maybe_cleanup_current_run_logs(self, *, force: bool = False) -> None:
        if not self._run_log_cleanup_enabled:
            return
        now = time()
        if (
            not force
            and self._run_log_cleanup_interval_seconds > 0
            and now - self._run_log_last_cleanup_at < self._run_log_cleanup_interval_seconds
        ):
            return
        self._run_log_last_cleanup_at = now

        try:
            files = [
                path
                for path in self.run_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
            ]
        except OSError:
            return
        if not files:
            return

        def file_info(path: Path) -> tuple[float, int]:
            try:
                stat = path.stat()
            except OSError:
                return (0.0, 0)
            return (stat.st_mtime, int(stat.st_size))

        protected = [path for path in files if self._is_protected_run_image(path)]
        regular = [path for path in files if path not in protected]
        regular.sort(key=lambda path: file_info(path)[0], reverse=True)

        delete_candidates: list[Path] = regular[self._run_log_keep_images :]
        retained_regular = regular[: self._run_log_keep_images]
        retained_size = sum(file_info(path)[1] for path in protected + retained_regular)

        if retained_size > self._run_log_max_bytes and len(retained_regular) > self._run_log_min_recent_images:
            extra_candidates = retained_regular[self._run_log_min_recent_images :]
            extra_candidates.sort(key=lambda path: file_info(path)[0])
            for path in extra_candidates:
                if retained_size <= self._run_log_max_bytes:
                    break
                retained_size -= file_info(path)[1]
                delete_candidates.append(path)

        deleted_count = 0
        deleted_bytes = 0
        for path in dict.fromkeys(delete_candidates):
            try:
                deleted_bytes += int(path.stat().st_size)
                path.unlink()
                deleted_count += 1
            except OSError:
                continue

        if deleted_count:
            self._record(
                {
                    "type": "state",
                    "state": "run_log_cleanup",
                    "deleted_files": deleted_count,
                    "deleted_mb": round(deleted_bytes / 1024 / 1024, 2),
                    "keep_images": self._run_log_keep_images,
                    "max_mb": round(self._run_log_max_bytes / 1024 / 1024, 2),
                }
            )

    def _watchdog_reset(self) -> None:
        self._watchdog_last_sample_at = 0.0
        self._watchdog_anchor_at = 0.0
        self._watchdog_anchor = None
        self._black_screen_started_at = 0.0
        self._black_screen_last_record_at = 0.0

    def _watchdog_mark_forward_progress(self, *, source: str) -> None:
        restart_streak = self._watchdog_restarts
        self._watchdog_reset()
        if restart_streak <= 0:
            return
        self._watchdog_restarts = 0
        self._record(
            {
                "type": "state",
                "state": "watchdog_restart_streak_reset",
                "source": source,
                "previous_restart_streak": restart_streak,
            }
        )

    @staticmethod
    def _watchdog_regions(image: np.ndarray) -> list[tuple[str, int, int, int, int]]:
        h, w = image.shape[:2]
        specs = (
            ("top_left", 0.06, 0.06, 0.22, 0.14),
            ("top_right", 0.72, 0.06, 0.22, 0.14),
            ("center", 0.36, 0.42, 0.28, 0.16),
            ("bottom_left", 0.06, 0.74, 0.22, 0.14),
            ("bottom_right", 0.72, 0.74, 0.22, 0.14),
        )
        regions: list[tuple[str, int, int, int, int]] = []
        for name, rx, ry, rw, rh in specs:
            x = max(0, min(int(w * rx), max(0, w - 2)))
            y = max(0, min(int(h * ry), max(0, h - 2)))
            width = max(1, min(int(w * rw), w - x))
            height = max(1, min(int(h * rh), h - y))
            regions.append((name, x, y, width, height))
        return regions

    @classmethod
    def _watchdog_fingerprints(cls, image: np.ndarray) -> dict[str, np.ndarray]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        samples: dict[str, np.ndarray] = {}
        for name, x, y, width, height in cls._watchdog_regions(image):
            crop = gray[y : y + height, x : x + width]
            samples[name] = cv2.resize(crop, (16, 12), interpolation=cv2.INTER_AREA).astype(np.float32)
        samples["__whole__"] = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(
            np.float32
        )
        return samples

    def _black_screen_metrics(self, image: np.ndarray) -> dict[str, float | bool]:
        h, w = image.shape[:2]
        top_skip = max(1, min(int(h * 0.12), max(1, h - 1)))
        crop = image[top_skip:h, 0:w]
        if crop.size == 0:
            crop = image

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        dark_ratio = float((gray <= self._black_screen_dark_threshold).mean()) if gray.size else 0.0
        mean_value = float(gray.mean()) if gray.size else 255.0
        std_value = float(gray.std()) if gray.size else 255.0
        edge_ratio = (
            float((cv2.Canny(gray, 20, 60) > 0).mean())
            if gray.shape[0] > 1 and gray.shape[1] > 1
            else 0.0
        )
        present = (
            dark_ratio >= self._black_screen_dark_ratio
            and mean_value <= self._black_screen_mean_threshold
            and edge_ratio <= self._black_screen_edge_ratio
        )
        return {
            "present": present,
            "dark_ratio": dark_ratio,
            "mean": mean_value,
            "std": std_value,
            "edge_ratio": edge_ratio,
        }

    def _restart_game_after_black_screen(
        self,
        *,
        source: str,
        elapsed_seconds: float,
        metrics: dict[str, float | bool],
        image: np.ndarray,
    ) -> None:
        self._watchdog_restarts += 1
        self._record(
            {
                "type": "state",
                "state": "black_screen_detected",
                "source": source,
                "elapsed_seconds": round(elapsed_seconds, 2),
                "dark_ratio": round(float(metrics.get("dark_ratio", 0.0)), 4),
                "mean": round(float(metrics.get("mean", 0.0)), 4),
                "edge_ratio": round(float(metrics.get("edge_ratio", 0.0)), 6),
                "restart_count": self._watchdog_restarts,
                "restart_limit": self._watchdog_restart_limit,
            }
        )
        self._save_image_snapshot("black_screen_detected", image)
        if self._watchdog_restarts > self._watchdog_restart_limit:
            raise RuntimeError(
                f"Black screen watchdog exceeded restart limit: {self._watchdog_restart_limit}."
            )

        self._watchdog_restarting = True
        try:
            self._check_stop_requested()
            self.bot.client.force_stop_package(self.package)
            self._record(
                {
                    "type": "state",
                    "state": "game_force_stopped_for_black_screen",
                    "package": self.package,
                    "restart_count": self._watchdog_restarts,
                }
            )
            self._sleep_with_watchdog(1.5, source="black_screen_restart_after_force_stop")
            self._check_stop_requested()
            self.bot.client.launch_package(self.package)
            self._record(
                {
                    "type": "state",
                    "state": "game_relaunched_after_black_screen",
                    "package": self.package,
                    "restart_count": self._watchdog_restarts,
                }
            )
            self._sleep_with_watchdog(10.0, source="black_screen_restart_after_launch")
            self._watchdog_reset()
            self.screenshot("after_black_screen_restart_launch")
        finally:
            self._watchdog_restarting = False

        raise SGZZScreenStuckRestart(
            f"Screen stayed black for {elapsed_seconds:.1f}s; game was restarted."
        )

    def _watchdog_maybe_handle_black_screen(
        self,
        *,
        source: str,
        image: np.ndarray,
        now: float,
    ) -> bool:
        metrics = self._black_screen_metrics(image)
        if not metrics["present"]:
            if self._black_screen_started_at > 0:
                elapsed_seconds = now - self._black_screen_started_at
                self._record(
                    {
                        "type": "state",
                        "state": "black_screen_recovered",
                        "source": source,
                        "elapsed_seconds": round(elapsed_seconds, 2),
                        "dark_ratio": round(float(metrics.get("dark_ratio", 0.0)), 4),
                        "mean": round(float(metrics.get("mean", 0.0)), 4),
                        "edge_ratio": round(float(metrics.get("edge_ratio", 0.0)), 6),
                    }
                )
            self._black_screen_started_at = 0.0
            self._black_screen_last_record_at = 0.0
            return False

        if self._black_screen_started_at <= 0:
            self._black_screen_started_at = now
            self._black_screen_last_record_at = now
            self._record(
                {
                    "type": "state",
                    "state": "black_screen_started",
                    "source": source,
                    "timeout_seconds": self._black_screen_timeout_seconds,
                    "dark_ratio": round(float(metrics.get("dark_ratio", 0.0)), 4),
                    "mean": round(float(metrics.get("mean", 0.0)), 4),
                    "edge_ratio": round(float(metrics.get("edge_ratio", 0.0)), 6),
                }
            )
            return True

        elapsed_seconds = now - self._black_screen_started_at
        if now - self._black_screen_last_record_at >= 5.0:
            self._black_screen_last_record_at = now
            self._record(
                {
                    "type": "state",
                    "state": "black_screen_still_present",
                    "source": source,
                    "elapsed_seconds": round(elapsed_seconds, 2),
                    "timeout_seconds": self._black_screen_timeout_seconds,
                    "dark_ratio": round(float(metrics.get("dark_ratio", 0.0)), 4),
                    "mean": round(float(metrics.get("mean", 0.0)), 4),
                    "edge_ratio": round(float(metrics.get("edge_ratio", 0.0)), 6),
                }
            )

        if elapsed_seconds >= self._black_screen_timeout_seconds:
            self._restart_game_after_black_screen(
                source=source,
                elapsed_seconds=elapsed_seconds,
                metrics=metrics,
                image=image,
            )
        return True

    def _finish_black_screen_watchdog_if_active(self, *, source: str) -> None:
        if not self._watchdog_enabled or self._watchdog_restarting:
            return

        now = time()
        image = self.bot.screenshot_image()
        metrics = self._black_screen_metrics(image)
        if not metrics["present"]:
            if self._black_screen_started_at > 0:
                self._watchdog_maybe_handle_black_screen(source=source, image=image, now=now)
            return

        self._watchdog_maybe_handle_black_screen(source=source, image=image, now=now)
        if self._black_screen_started_at <= 0:
            return

        elapsed_seconds = time() - self._black_screen_started_at
        remaining_seconds = self._black_screen_timeout_seconds - elapsed_seconds
        if remaining_seconds > 0:
            self._record(
                {
                    "type": "state",
                    "state": "black_screen_watchdog_grace_wait",
                    "source": source,
                    "elapsed_seconds": round(elapsed_seconds, 2),
                    "timeout_seconds": self._black_screen_timeout_seconds,
                    "remaining_seconds": round(remaining_seconds, 2),
                    "dark_ratio": round(float(metrics.get("dark_ratio", 0.0)), 4),
                    "mean": round(float(metrics.get("mean", 0.0)), 4),
                    "edge_ratio": round(float(metrics.get("edge_ratio", 0.0)), 6),
                }
            )
            self._sleep_with_watchdog(remaining_seconds + 0.8, source=source)

        self._watchdog_maybe_check(source=source, force=True)

    def _restart_game_after_stuck(
        self,
        *,
        source: str,
        elapsed_seconds: float,
        stable_regions: list[str],
        diffs: dict[str, float],
        image: np.ndarray,
    ) -> None:
        self._watchdog_restarts += 1
        self._record(
            {
                "type": "state",
                "state": "screen_stuck_detected",
                "source": source,
                "elapsed_seconds": round(elapsed_seconds, 2),
                "stable_regions": stable_regions,
                "stable_region_count": len(stable_regions),
                "diffs": {key: round(value, 4) for key, value in diffs.items()},
                "restart_count": self._watchdog_restarts,
                "restart_limit": self._watchdog_restart_limit,
            }
        )
        self._save_image_snapshot("screen_stuck_detected", image)
        if self._watchdog_restarts > self._watchdog_restart_limit:
            raise RuntimeError(
                f"Screen stuck watchdog exceeded restart limit: {self._watchdog_restart_limit}."
            )

        self._watchdog_restarting = True
        try:
            self._check_stop_requested()
            self.bot.client.force_stop_package(self.package)
            self._record(
                {
                    "type": "state",
                    "state": "game_force_stopped_for_stuck",
                    "package": self.package,
                    "restart_count": self._watchdog_restarts,
                }
            )
            self._sleep_with_watchdog(1.5, source="stuck_restart_after_force_stop")
            self._check_stop_requested()
            self.bot.client.launch_package(self.package)
            self._record(
                {
                    "type": "state",
                    "state": "game_relaunched_after_stuck",
                    "package": self.package,
                    "restart_count": self._watchdog_restarts,
                }
            )
            self._sleep_with_watchdog(10.0, source="stuck_restart_after_launch")
            self._watchdog_reset()
            self.screenshot("after_stuck_restart_launch")
        finally:
            self._watchdog_restarting = False

        raise SGZZScreenStuckRestart(
            f"Screen stayed static for {elapsed_seconds:.1f}s; game was restarted."
        )

    def _recover_external_foreground_if_needed(
        self,
        *,
        source: str,
        image: np.ndarray | None = None,
        force: bool = False,
    ) -> bool:
        now = time()
        if (
            not force
            and now - self._foreground_last_check_at < self._foreground_check_interval_seconds
        ):
            return False
        self._foreground_last_check_at = now

        try:
            focus = self.bot.client.current_focus()
        except Exception as exc:
            self._record(
                {
                    "type": "state",
                    "state": "foreground_check_failed",
                    "source": source,
                    "error": str(exc),
                }
            )
            return False

        if not focus or self.package in focus:
            return False

        known_external_markers = (
            "com.android.permissioncontroller",
            "com.google.android.permissioncontroller",
            OVERLAY_BRIDGE_PACKAGE,
            "com.android.settings",
            "com.miui.home",
            "com.android.launcher",
        )
        if not any(marker in focus for marker in known_external_markers):
            return False

        self._watchdog_restarts += 1
        self._record(
            {
                "type": "state",
                "state": "external_foreground_recovery",
                "source": source,
                "focus": focus,
                "package": self.package,
                "restart_count": self._watchdog_restarts,
                "restart_limit": self._watchdog_restart_limit,
            }
        )
        if image is not None:
            self._save_image_snapshot("external_foreground_recovery", image)
        if self._watchdog_restarts > self._watchdog_restart_limit:
            raise RuntimeError(
                f"External foreground recovery exceeded restart limit: {self._watchdog_restart_limit}."
            )

        self._watchdog_restarting = True
        try:
            if "permissioncontroller" in focus:
                try:
                    self.bot.client.shell(
                        [
                            "pm",
                            "grant",
                            OVERLAY_BRIDGE_PACKAGE,
                            "android.permission.POST_NOTIFICATIONS",
                        ],
                        timeout=5.0,
                    )
                    self._record(
                        {
                            "type": "state",
                            "state": "overlay_notification_permission_granted",
                            "package": OVERLAY_BRIDGE_PACKAGE,
                        }
                    )
                except Exception as exc:
                    self._record(
                        {
                            "type": "state",
                            "state": "overlay_notification_permission_grant_failed",
                            "package": OVERLAY_BRIDGE_PACKAGE,
                            "error": str(exc),
                        }
                    )
                try:
                    width, height = self.bot.client.get_screen_size()
                    self.bot.client.tap(width // 2, int(height * 0.57))
                    self._record(
                        {
                            "type": "tap",
                            "label": "系统权限弹窗-允许",
                            "x": width // 2,
                            "y": int(height * 0.57),
                        }
                    )
                except Exception as exc:
                    self._record(
                        {
                            "type": "state",
                            "state": "permission_allow_tap_failed",
                            "error": str(exc),
                        }
                    )
                sleep(1.0)

            self._check_stop_requested()
            self.bot.client.launch_package(self.package)
            self._record(
                {
                    "type": "state",
                    "state": "game_relaunched_after_external_foreground",
                    "focus": focus,
                    "package": self.package,
                }
            )
            sleep(5.0)
            self._watchdog_reset()
            try:
                recovered_image = self.bot.screenshot_image()
                self._save_image_snapshot("after_external_foreground_recovery", recovered_image)
            except Exception as exc:
                self._record(
                    {
                        "type": "state",
                        "state": "after_external_foreground_recovery_screenshot_failed",
                        "error": str(exc),
                    }
                )
        finally:
            self._watchdog_restarting = False
        return True

    def _watchdog_maybe_check(
        self,
        *,
        source: str,
        image: np.ndarray | None = None,
        force: bool = False,
    ) -> None:
        if not self._watchdog_enabled or self._watchdog_restarting:
            return
        now = time()
        if not force and now - self._watchdog_last_sample_at < self._watchdog_sample_interval_seconds:
            return
        if image is None:
            image = self.bot.screenshot_image()
        if self._recover_external_foreground_if_needed(source=source, image=image, force=force):
            return
        if self._watchdog_maybe_handle_black_screen(source=source, image=image, now=now):
            self._watchdog_last_sample_at = now
            return
        current = self._watchdog_fingerprints(image)
        self._watchdog_last_sample_at = now
        if self._watchdog_anchor is None or set(current) != set(self._watchdog_anchor):
            self._watchdog_anchor = current
            self._watchdog_anchor_at = now
            return

        diffs = {
            name: float(np.abs(current[name] - self._watchdog_anchor[name]).mean())
            for name in current
        }
        whole_diff = diffs.pop("__whole__", 0.0)
        progress_regions = [
            name for name, diff in diffs.items() if diff >= self._watchdog_progress_diff_threshold
        ]
        if whole_diff >= self._watchdog_whole_progress_diff_threshold:
            progress_regions.append("__whole__")
        if progress_regions:
            self._watchdog_anchor = current
            self._watchdog_anchor_at = now
            return

        stable_regions = [
            name for name, diff in diffs.items() if diff <= self._watchdog_diff_threshold
        ]
        if len(stable_regions) < self._watchdog_min_static_regions:
            self._watchdog_anchor = current
            self._watchdog_anchor_at = now
            return

        elapsed_seconds = now - self._watchdog_anchor_at
        if elapsed_seconds >= self._watchdog_timeout_seconds:
            self._restart_game_after_stuck(
                source=source,
                elapsed_seconds=elapsed_seconds,
                stable_regions=stable_regions,
                diffs={"__whole__": whole_diff, **diffs},
                image=image,
            )

    def _sleep_with_watchdog(self, seconds: float, *, source: str) -> None:
        end_at = time() + max(0.0, seconds)
        self._check_stop_requested()
        while time() < end_at:
            sleep(min(0.5, max(0.0, end_at - time())))
            self._check_stop_requested()
            self._watchdog_maybe_check(source=f"sleep:{source}")

    def screenshot(self, label: str) -> Path:
        self._check_stop_requested()
        self._step_index += 1
        data = self.bot.client.screencap_png()
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        path = self._snapshot_path(label)
        if image is None or self._screenshot_format == "png":
            if path.suffix.lower() != ".png":
                path = path.with_suffix(".png")
            path.write_bytes(data)
        else:
            self._write_snapshot_image(path, image)
        self._record({"type": "screenshot", "label": label, "path": str(path)})
        if image is not None:
            self._watchdog_maybe_check(source=f"screenshot:{label}", image=image)
        self._maybe_cleanup_current_run_logs()
        return path

    @staticmethod
    def _clip_region(
        image: np.ndarray,
        region: tuple[int, int, int, int],
    ) -> tuple[int, int, int, int]:
        h, w = image.shape[:2]
        x, y, width, height = [int(v) for v in region]
        x = max(0, min(x, max(0, w - 1)))
        y = max(0, min(y, max(0, h - 1)))
        width = max(1, min(width, w - x))
        height = max(1, min(height, h - y))
        return x, y, width, height

    def save_crop(
        self,
        label: str,
        image: np.ndarray,
        region: tuple[int, int, int, int],
    ) -> Path:
        self._check_stop_requested()
        x, y, width, height = self._clip_region(image, region)
        crop = image[y : y + height, x : x + width]
        self._step_index += 1
        name = f"{self.run_id}_{self._step_index:03d}_{label}.png"
        path = self.run_dir / name
        cv2.imwrite(str(path), crop)
        self._record(
            {
                "type": "screenshot_crop",
                "label": label,
                "path": str(path),
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            }
        )
        self._maybe_cleanup_current_run_logs()
        return path

    @staticmethod
    def _crop(image: np.ndarray, region: tuple[int, int, int, int]) -> np.ndarray:
        x, y, width, height = SGZZStartAccountRunner._clip_region(image, region)
        return image[y : y + height, x : x + width]

    @staticmethod
    def _template_similarity(haystack: np.ndarray, template: np.ndarray) -> float:
        if haystack.size == 0 or template.size == 0:
            return 0.0
        if haystack.shape[0] < template.shape[0] or haystack.shape[1] < template.shape[1]:
            return 0.0
        result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return float(max_val)

    def _find_template_in_image(
        self,
        image: np.ndarray,
        template_key: str,
        *,
        threshold: float = 0.86,
        region: tuple[int, int, int, int] | None = None,
    ) -> Match | None:
        template_path = Path(TEMPLATES[template_key])
        if not template_path.is_absolute():
            template_path = self.bot.config.template_dir / template_path
        return match_template(image, template_path, threshold=threshold, region=region)

    def detect_server_selector_title_in_image(
        self,
        image: np.ndarray,
        *,
        threshold: float = 0.82,
    ) -> Match | None:
        h, w = image.shape[:2]
        return self._find_template_in_image(
            image,
            "server_selector_title",
            threshold=threshold,
            region=(int(w * 0.20), int(h * 0.06), int(w * 0.60), int(h * 0.16)),
        )

    def detect_exit_confirm_in_image(
        self,
        image: np.ndarray,
        *,
        threshold: float = 0.72,
    ) -> Match | None:
        h, w = image.shape[:2]
        return self._find_template_in_image(
            image,
            "exit_confirm_title",
            threshold=threshold,
            region=(int(w * 0.22), int(h * 0.35), int(w * 0.58), int(h * 0.18)),
        )

    def detect_soft_keyboard_visible(self, image: np.ndarray) -> bool:
        h, w = image.shape[:2]
        bottom = image[int(h * 0.62) : h, 0:w]
        gray = cv2.cvtColor(bottom, cv2.COLOR_BGR2GRAY)
        bright_ratio = float((gray > 210).mean()) if gray.size else 0.0
        edge_ratio = float((cv2.Canny(gray, 60, 120) > 0).mean()) if gray.size else 0.0
        present = bright_ratio > 0.18 and edge_ratio > 0.045
        self._record(
            {
                "type": "vision_feature",
                "feature": "soft_keyboard_visible",
                "present": present,
                "bright_ratio": round(bright_ratio, 4),
                "edge_ratio": round(edge_ratio, 4),
            }
        )
        return present

    def tap(self, label: str, point: Point, *, wait_seconds: float = 0.0) -> None:
        self._check_stop_requested()
        self._step_index += 1
        self.bot.tap(point.x, point.y, jitter=0)
        self._record(
            {
                "type": "tap",
                "label": label,
                "x": point.x,
                "y": point.y,
                "step": self._step_index,
            }
        )
        if wait_seconds > 0:
            self._sleep_with_watchdog(wait_seconds, source=label)

    def wait_for_template(
        self,
        label: str,
        template_key: str,
        *,
        timeout_seconds: float = 3.0,
        threshold: float = 0.86,
        region: tuple[int, int, int, int] | None = None,
    ) -> Match | None:
        template = TEMPLATES[template_key]
        end_at = time() + timeout_seconds
        while time() < end_at:
            self._check_stop_requested()
            match = self.bot.find_image(template, threshold=threshold, region=region)
            if match:
                self._record(
                    {
                        "type": "match",
                        "label": label,
                        "template": template,
                        "x": match.x,
                        "y": match.y,
                        "width": match.width,
                        "height": match.height,
                        "score": round(match.score, 4),
                    }
                )
                return match
            remaining = end_at - time()
            if remaining <= 0:
                break
            self._sleep_with_watchdog(min(0.25, remaining), source=label)
        self._record(
            {
                "type": "match_miss",
                "label": label,
                "template": template,
                "timeout_seconds": timeout_seconds,
            }
        )
        return None

    def click_template_or_point(
        self,
        label: str,
        template_key: str,
        fallback: Point,
        *,
        timeout_seconds: float = 3.0,
        threshold: float = 0.86,
        region: tuple[int, int, int, int] | None = None,
        wait_seconds: float = 0.0,
    ) -> None:
        match = self.wait_for_template(
            label,
            template_key,
            timeout_seconds=timeout_seconds,
            threshold=threshold,
            region=region,
        )
        if match:
            x, y = match.center
            self.tap(f"{label}-模板命中", Point(x, y), wait_seconds=wait_seconds)
            return
        self.tap(f"{label}-备用坐标", fallback, wait_seconds=wait_seconds)

    def launch(self, wait_seconds: float = 8.0) -> None:
        self._check_stop_requested()
        self._record({"type": "state", "state": "launch_game", "package": self.package})
        self._watchdog_reset()
        self.bot.client.launch_package(self.package)
        self._sleep_with_watchdog(wait_seconds, source="launch_game")
        self.screenshot("after_launch")

    def select_account_client(
        self,
        credential: SGZZAccountCredential,
        *,
        restart_if_changed: bool,
    ) -> None:
        previous_client = self.client_name
        previous_package = self.package
        self.client_name = credential.client
        self.package = credential.package
        changed = previous_package != self.package
        self._record(
            {
                "type": "state",
                "state": "account_client_selected",
                "account": credential.masked_account,
                "account_key": credential.account_key,
                "client": credential.client,
                "package": credential.package,
                "previous_client": previous_client,
                "previous_package": previous_package,
                "package_changed": changed,
            }
        )
        if not changed or not restart_if_changed:
            return

        self.bot.client.force_stop_package(previous_package)
        self.bot.client.force_stop_package(self.package)
        self._sleep_with_watchdog(1.0, source="account_client_switch_force_stop")
        self.launch(wait_seconds=8.0)
        self.screenshot(f"after_account_client_switch_{credential.client}")

    def dismiss_restore_prompt(self) -> None:
        self._record({"type": "state", "state": "dismiss_restore_prompt"})
        match = self.wait_for_template(
            "恢复隐藏角色弹窗-取消",
            "restore_cancel_button",
            timeout_seconds=2.0,
            threshold=0.82,
            region=(330, 680, 240, 140),
        )
        if match:
            self.tap("恢复隐藏角色弹窗-取消", Point(*match.center), wait_seconds=1.0)
            self.screenshot("after_restore_cancel")
        else:
            self._record({"type": "state", "state": "restore_prompt_not_seen"})

    def detect_title_login_in_progress(
        self,
        image: np.ndarray | None = None,
        *,
        source: str,
        record: bool = True,
    ) -> bool:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            if record:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "title_login_in_progress",
                        "present": False,
                        "source": source,
                        "reason": "landscape_screen",
                    }
                )
            return False

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        overlay_region = (int(w * 0.32), int(h * 0.43), int(w * 0.36), int(h * 0.16))
        spinner_region = (int(w * 0.38), int(h * 0.43), int(w * 0.24), int(h * 0.10))
        select_region = (int(w * 0.55), int(h * 0.67), int(w * 0.26), int(h * 0.08))
        ox, oy, ow, oh = self._clip_region(image, overlay_region)
        sx, sy, sw, sh = self._clip_region(image, spinner_region)
        bx, by, bw, bh = self._clip_region(image, select_region)
        overlay = gray[oy : oy + oh, ox : ox + ow]
        spinner = gray[sy : sy + sh, sx : sx + sw]
        select = gray[by : by + bh, bx : bx + bw]

        overlay_dark_ratio = float((overlay < 70).mean()) if overlay.size else 0.0
        spinner_dark_ratio = float((spinner < 70).mean()) if spinner.size else 0.0
        spinner_edge_ratio = (
            float((cv2.Canny(spinner, 60, 140) > 0).mean()) if spinner.size else 0.0
        )
        select_dark_ratio = float((select < 70).mean()) if select.size else 0.0

        present = (
            overlay_dark_ratio >= 0.78
            and spinner_dark_ratio >= 0.68
            and spinner_edge_ratio >= 0.08
            and select_dark_ratio >= 0.86
        )
        if record:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "title_login_in_progress",
                    "present": present,
                    "source": source,
                    "overlay_dark_ratio": round(overlay_dark_ratio, 3),
                    "spinner_dark_ratio": round(spinner_dark_ratio, 3),
                    "spinner_edge_ratio": round(spinner_edge_ratio, 3),
                    "select_dark_ratio": round(select_dark_ratio, 3),
                }
            )
        return present

    def wait_for_title_login_in_progress_clear(
        self,
        *,
        timeout_seconds: float,
        source: str,
    ) -> bool:
        end_at = time() + max(0.1, timeout_seconds)
        seen = False
        while time() < end_at:
            image = self.bot.screenshot_image()
            if not self.detect_title_login_in_progress(image, source=source):
                if seen:
                    self.screenshot(f"{source}_title_login_in_progress_cleared")
                return seen
            seen = True
            self._sleep_with_watchdog(0.8, source=f"title_login_in_progress:{source}")
        if seen:
            self.screenshot(f"{source}_title_login_in_progress_still_visible")
        return seen

    def open_server_selector(self) -> None:
        self._record({"type": "state", "state": "open_server_selector"})
        self.close_exit_confirm_if_present(timeout_seconds=0.2)
        if self.click_recent_login_account_if_present(timeout_seconds=0.3):
            self.click_account_login_modal_if_present(timeout_seconds=2.0)

        self.wait_for_title_login_in_progress_clear(
            timeout_seconds=35.0,
            source="open_server_selector_initial",
        )

        image = self.bot.screenshot_image()
        opened = self.detect_server_selector_title_in_image(image)
        if opened:
            self.screenshot("server_selector")
            return

        for attempt in range(1, 4):
            self.close_exit_confirm_if_present(timeout_seconds=0.2)
            self.wait_for_title_login_in_progress_clear(
                timeout_seconds=20.0,
                source=f"open_server_selector_before_tap_{attempt}",
            )
            self.click_template_or_point(
                f"标题页-点击选服#{attempt}",
                "title_select_server",
                self.coords.title_select_server,
                timeout_seconds=1.2,
                threshold=0.80,
                region=(380, 860, 220, 120),
                wait_seconds=0.8,
            )
            opened = self.wait_for_template(
                f"选服弹窗标题#{attempt}",
                "server_selector_title",
                timeout_seconds=1.4,
                threshold=0.82,
                region=(210, 90, 300, 100),
            )
            if opened:
                self.screenshot("server_selector")
                return
            self.wait_for_title_login_in_progress_clear(
                timeout_seconds=25.0,
                source=f"open_server_selector_after_tap_{attempt}",
            )
            self.close_exit_confirm_if_present(timeout_seconds=0.2)
            self.screenshot(f"server_selector_open_retry_{attempt}_not_found")

        self.screenshot("server_selector_open_failed")
        raise RuntimeError("Server selector did not open; refusing to continue role selection.")

    def close_server_selector_for_account_switch_if_open(
        self,
        image: np.ndarray | None = None,
        *,
        source: str,
    ) -> bool:
        if image is None:
            image = self.bot.screenshot_image()
        selector = self.detect_server_selector_title_in_image(image, threshold=0.74)
        if not selector:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "server_selector_close_for_account_switch",
                    "present": False,
                    "source": source,
                }
            )
            return False

        h, w = image.shape[:2]
        close_region = (int(w * 0.84), int(h * 0.07), int(w * 0.14), int(h * 0.10))
        close_button = self._find_red_dot(image, close_region)
        point = Point(*close_button.center) if close_button else Point(int(w * 0.918), int(h * 0.112))
        self._record(
            {
                "type": "vision_feature",
                "feature": "server_selector_close_for_account_switch",
                "present": True,
                "source": source,
                "title_x": selector.x,
                "title_y": selector.y,
                "title_width": selector.width,
                "title_height": selector.height,
                "title_score": round(selector.score, 4),
                "close_source": "red_dot" if close_button else "coordinate_fallback",
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("账号批量-关闭选服弹窗", point, wait_seconds=0.8)

        check_image = self.bot.screenshot_image()
        still_open = self.detect_server_selector_title_in_image(check_image, threshold=0.74)
        self._record(
            {
                "type": "vision_feature",
                "feature": "server_selector_close_for_account_switch_check",
                "still_open": still_open is not None,
                "source": source,
                "score": round(still_open.score, 4) if still_open else 0.0,
            }
        )
        if still_open:
            self.tap("账号批量-关闭选服弹窗-复点", Point(int(w * 0.918), int(h * 0.112)), wait_seconds=1.0)
        return True

    def tap_server_selector_confirm(self, label: str, *, wait_seconds: float = 1.2) -> None:
        self._record(
            {
                "type": "vision_feature",
                "feature": "server_selector_confirm_button",
                "source": "known_selector_button",
                "x": self.coords.server_confirm.x,
                "y": self.coords.server_confirm.y,
            }
        )
        self.tap(label, self.coords.server_confirm, wait_seconds=0.8)
        still_open = self.wait_for_template(
            f"{label}-弹窗复查",
            "server_selector_title",
            timeout_seconds=0.45,
            threshold=0.82,
            region=(210, 90, 300, 100),
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "server_selector_confirm_after_tap",
                "selector_still_open": still_open is not None,
                "x": still_open.x if still_open else None,
                "y": still_open.y if still_open else None,
                "score": round(still_open.score, 4) if still_open else 0.0,
            }
        )
        if still_open:
            self.tap(f"{label}-复点", self.coords.server_confirm, wait_seconds=wait_seconds)
        else:
            self._sleep_with_watchdog(max(0.0, wait_seconds - 0.8), source=label)

    def detect_server_selector_bounds(self, image: np.ndarray | None = None) -> tuple[int, int, int]:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        match = self.detect_server_selector_title_in_image(image, threshold=0.76)
        if match is None:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "server_selector_bounds",
                    "source": "selector_title_not_visible",
                    "screen_width": w,
                    "screen_height": h,
                }
            )
            self.close_exit_confirm_if_present(timeout_seconds=0.2)
            raise RuntimeError("Server selector title is not visible; refusing to infer selector bounds.")

        y_top = int(match.y + match.height + 90)
        row_mean = image.mean(axis=(1, 2))

        # Use near-bottom non-dark content to define the scrollable range.
        y_bottom = int(h - 120)
        for y in range(h - 1, y_top - 1, -1):
            if row_mean[y] > 30:
                y_bottom = y - 20
                break

        y_bottom = int(min(y_bottom, h - 120))
        y_top = int(max(y_top, h * 0.18, 180))
        y_bottom = int(max(y_top + 180, y_bottom))

        center_x = int(match.x + match.width / 2)
        self._record(
            {
                "type": "vision_feature",
                "feature": "server_selector_bounds",
                "source": "template_and_row_scan",
                "title_x": match.x,
                "title_y": match.y,
                "title_width": match.width,
                "title_height": match.height,
                "title_center_x": center_x,
                "title_center_y": int(match.y + match.height / 2),
                "scroll_top": y_top,
                "scroll_bottom": y_bottom,
                "screen_width": w,
                "screen_height": h,
            }
        )
        return center_x, y_top, y_bottom

    @staticmethod
    def _roi_change_score(image_a: np.ndarray, image_b: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> float:
        if x1 >= x2 or y1 >= y2:
            return 0.0
        gray_a = cv2.cvtColor(image_a[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(image_b[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        if gray_a.shape != gray_b.shape:
            return 999.0
        return float(cv2.absdiff(gray_a, gray_b).mean())

    @staticmethod
    def _roi_changed(image_a: np.ndarray, image_b: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> bool:
        if image_a.shape != image_b.shape:
            return True
        return SGZZStartAccountRunner._roi_change_score(image_a, image_b, x1, y1, x2, y2) > 0.2

    def detect_server_selector_role_rows(self) -> list[dict[str, int | float]]:
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        title = self.detect_server_selector_title_in_image(image, threshold=0.76)
        if not title:
            self.close_exit_confirm_if_present(timeout_seconds=0.2)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "server_selector_role_rows",
                    "source": "selector_title_not_visible",
                    "rows": [],
                }
            )
            return []

        center_x, top, bottom = self.detect_server_selector_bounds(image)
        x1 = 20
        x2 = min(170, w)
        y1 = max(180, top - 20)
        y2 = min(bottom, int(h * 0.78))
        crop = image[y1:y2, x1:x2]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        mask = ((hsv[:, :, 1] > 50) & (hsv[:, :, 2] > 45)).astype("uint8") * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

        min_area = max(120, int(h * w * 0.0008))
        min_height = max(20, int(h * 0.026))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rows: list[dict[str, int | float]] = []
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            area = float(cv2.contourArea(contour))
            if area < min_area:
                continue
            if not (min_height <= height <= 80 and 22 <= width <= 80):
                continue
            aspect = width / float(height)
            if not (0.55 <= aspect <= 1.8):
                continue

            absolute_x = int(x1 + x)
            absolute_y = int(y1 + y)
            row = {
                "x": absolute_x,
                "y": absolute_y,
                "width": int(width),
                "height": int(height),
                "center_x": int(absolute_x + width / 2),
                "center_y": int(absolute_y + height / 2),
                "tap_x": int(center_x),
                "tap_y": int(absolute_y + height / 2),
                "area": round(area, 2),
            }
            rows.append(row)

        rows.sort(key=lambda item: int(item["center_y"]))

        # The currently selected role avatar is rendered with much lower saturation,
        # so the color mask above can omit exactly the row we need to keep selected.
        # Recover missing row slots from the regular row cadence, but only when the
        # avatar-sized ROI still contains enough grayscale detail to be occupied.
        inferred_rows: list[dict[str, int | float | bool]] = []
        if len(rows) >= 4:
            centers = [int(item["center_y"]) for item in rows]
            regular_gaps = [
                right - left
                for left, right in zip(centers, centers[1:])
                if 58 <= right - left <= 88
            ]
            if regular_gaps:
                row_step = int(round(float(np.median(regular_gaps))))
                candidate_centers: list[int] = []
                for left, right in zip(centers, centers[1:]):
                    if row_step * 1.6 <= right - left <= row_step * 2.4:
                        candidate_centers.append(left + row_step)

                trailing_center = centers[-1] + row_step
                if (
                    len(rows) >= 6
                    and centers[0] <= int(h * 0.23)
                    and trailing_center <= int(h * 0.56)
                ):
                    candidate_centers.append(trailing_center)

                avatar_center_x = int(round(float(np.median([int(item["center_x"]) for item in rows]))))
                for candidate_center in sorted(set(candidate_centers)):
                    avatar_x1 = max(0, avatar_center_x - 28)
                    avatar_x2 = min(w, avatar_center_x + 28)
                    avatar_y1 = max(0, candidate_center - 28)
                    avatar_y2 = min(h, candidate_center + 28)
                    avatar_crop = image[avatar_y1:avatar_y2, avatar_x1:avatar_x2]
                    if avatar_crop.size == 0:
                        continue
                    avatar_gray = cv2.cvtColor(avatar_crop, cv2.COLOR_BGR2GRAY)
                    avatar_edges = cv2.Canny(avatar_gray, 45, 120)
                    gray_std = float(avatar_gray.std())
                    edge_ratio = float((avatar_edges > 0).mean())
                    occupied = gray_std >= 14.0 and edge_ratio >= 0.045
                    self._record(
                        {
                            "type": "vision_feature",
                            "feature": "server_selector_inferred_role_row_candidate",
                            "center_y": candidate_center,
                            "gray_std": round(gray_std, 4),
                            "edge_ratio": round(edge_ratio, 6),
                            "occupied": occupied,
                        }
                    )
                    if not occupied:
                        continue
                    inferred_rows.append(
                        {
                            "x": avatar_center_x - 24,
                            "y": candidate_center - 24,
                            "width": 48,
                            "height": 48,
                            "center_x": avatar_center_x,
                            "center_y": candidate_center,
                            "tap_x": int(center_x),
                            "tap_y": candidate_center,
                            "area": 0.0,
                            "inferred_selected": True,
                        }
                    )

        if inferred_rows:
            existing_centers = [int(item["center_y"]) for item in rows]
            for inferred_row in inferred_rows:
                inferred_center = int(inferred_row["center_y"])
                if all(abs(inferred_center - center) > 24 for center in existing_centers):
                    rows.append(inferred_row)
                    existing_centers.append(inferred_center)
            rows.sort(key=lambda item: int(item["center_y"]))
        self._record(
            {
                "type": "vision_feature",
                "feature": "server_selector_role_rows",
                "search_x1": x1,
                "search_y1": y1,
                "search_x2": x2,
                "search_y2": y2,
                "min_area": min_area,
                "min_height": min_height,
                "rows": rows,
            }
        )
        return rows

    def detect_hidden_role_restore_buttons(self, image: np.ndarray | None = None) -> list[Match]:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (int(w * 0.70), int(h * 0.22), int(w * 0.27), int(h * 0.66))
        x, y, width, height = self._clip_region(image, region)
        crop = image[y : y + height, x : x + width]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([35, 40, 35]), np.array([100, 255, 210]))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        buttons: list[Match] = []
        for contour in contours:
            area = float(cv2.contourArea(contour))
            box_x, box_y, box_w, box_h = cv2.boundingRect(contour)
            if area < 900:
                continue
            if not (70 <= box_w <= 170 and 20 <= box_h <= 48):
                continue
            buttons.append(
                Match(
                    x=int(x + box_x),
                    y=int(y + box_y),
                    width=int(box_w),
                    height=int(box_h),
                    score=area,
                    kind="hidden_role_restore_button",
                )
            )
        buttons.sort(key=lambda item: item.y)
        self._record(
            {
                "type": "vision_feature",
                "feature": "hidden_role_restore_buttons",
                "count": len(buttons),
                "region_x": x,
                "region_y": y,
                "region_width": width,
                "region_height": height,
                "buttons": [
                    {
                        "x": button.x,
                        "y": button.y,
                        "width": button.width,
                        "height": button.height,
                        "score": round(button.score, 1),
                    }
                    for button in buttons
                ],
            }
        )
        return buttons

    def restore_hidden_role_from_selector_if_available(self) -> bool:
        self._record({"type": "state", "state": "restore_hidden_role_from_selector_if_available"})
        self.screenshot("before_restore_hidden_role_from_selector")
        self.tap("选服列表-打开隐藏显示角色", self.coords.server_hidden_roles_toggle, wait_seconds=1.0)
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        buttons = self.detect_hidden_role_restore_buttons(image)
        if not buttons:
            close_button = self._find_red_dot(image, (int(w * 0.84), int(h * 0.16), int(w * 0.14), int(h * 0.12)))
            point = Point(*close_button.center) if close_button else Point(int(w * 0.92), int(h * 0.205))
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "hidden_role_restore_unavailable",
                    "close_source": "red_button" if close_button else "fallback",
                    "tap_x": point.x,
                    "tap_y": point.y,
                }
            )
            self.tap("选服列表-关闭隐藏角色面板", point, wait_seconds=0.8)
            self.screenshot("hidden_role_restore_unavailable")
            return False

        target = buttons[-1]
        point = Point(*target.center)
        self._record(
            {
                "type": "vision_feature",
                "feature": "hidden_role_restore_selected",
                "x": target.x,
                "y": target.y,
                "width": target.width,
                "height": target.height,
                "score": round(target.score, 1),
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("选服列表-恢复隐藏角色", point, wait_seconds=1.4)
        self.screenshot("after_restore_hidden_role_from_selector")
        return True

    def fingerprint_server_selector_role_row(
        self,
        row: dict[str, int | float],
        image: np.ndarray | None = None,
    ) -> str:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        row_y = int(row["y"])
        row_h = int(row["height"])
        x1 = max(0, int(w * 0.03))
        x2 = min(w, int(w * 0.92))
        y1 = max(0, row_y - 10)
        y2 = min(h, row_y + row_h + 26)
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return ""
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (32, 16), interpolation=cv2.INTER_AREA)
        bits = (small > float(np.median(small))).astype(np.uint8).reshape(-1)
        return np.packbits(bits).tobytes().hex()

    @staticmethod
    def server_selector_role_identity_region(
        row: dict[str, int | float],
        image: np.ndarray,
    ) -> tuple[int, int, int, int]:
        h, w = image.shape[:2]
        row_y = int(row["y"])
        row_h = int(row["height"])
        x1 = max(0, int(w * 0.04))
        x2 = min(w, int(w * 0.88))
        y1 = max(0, row_y - 8)
        y2 = min(h, row_y + row_h + 18)
        return x1, y1, x2 - x1, y2 - y1

    @staticmethod
    def title_role_identity_region(image: np.ndarray) -> tuple[int, int, int, int]:
        h, w = image.shape[:2]
        return int(w * 0.24), int(h * 0.675), int(w * 0.25), int(h * 0.045)

    @staticmethod
    def ingame_role_identity_region(image: np.ndarray) -> tuple[int, int, int, int]:
        h, w = image.shape[:2]
        # Match the role-name line only. The old crop included the avatar, resource
        # counters and fixed title suffix, which made different new roles look alike.
        return int(w * 0.12), int(h * 0.098), int(w * 0.29), int(h * 0.032)

    def compare_role_identity_crop(
        self,
        *,
        label: str,
        image: np.ndarray,
        region: tuple[int, int, int, int],
        template: np.ndarray | None,
    ) -> float:
        if template is None:
            score = 0.0
        else:
            crop = self._crop(image, region)
            score = self._template_similarity(crop, template)
        x, y, width, height = self._clip_region(image, region)
        self._record(
            {
                "type": "vision_feature",
                "feature": "role_identity_similarity",
                "label": label,
                "score": round(score, 4),
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "has_template": template is not None,
            }
        )
        return score

    def scroll_server_selector_to_bottom(self, *, swipe_count: int = 3) -> Path:
        self._record(
            {
                "type": "state",
                "state": "scroll_server_selector_to_bottom",
                "swipe_count": swipe_count,
            }
        )
        pull_count = min(max(1, swipe_count), 3)
        for index in range(pull_count):
            before = self.bot.screenshot_image()
            h, w = before.shape[:2]
            swipe_x = int(w * 0.125)
            start_y = int(h * 0.54)
            end_y = int(h * 0.20)
            list_top = int(h * 0.18)
            list_bottom = int(h * 0.62)
            roi_x1 = int(w * 0.03)
            roi_x2 = int(w * 0.94)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "server_selector_scroll_points",
                    "index": index,
                    "list_top": list_top,
                    "list_bottom": list_bottom,
                    "start_y": start_y,
                    "end_y": end_y,
                    "swipe_x": swipe_x,
                    "change_roi_x1": roi_x1,
                    "change_roi_x2": roi_x2,
                    "max_pulls": pull_count,
                }
            )

            self.bot.swipe(swipe_x, start_y, swipe_x, end_y, 380)
            self._sleep_with_watchdog(0.45, source="server_selector_scroll")
            after = self.bot.screenshot_image()
            change_score = self._roi_change_score(before, after, roi_x1, list_top, roi_x2, list_bottom)
            changed = change_score > 1.0
            self.screenshot(f"server_selector_swipe_{index:02d}_{'changed' if changed else 'static'}")
            self._record(
                {
                    "type": "state",
                    "state": "server_selector_swipe",
                    "index": index,
                    "changed": changed,
                    "used_x": swipe_x,
                    "change_score": round(change_score, 4),
                }
            )
            if not changed:
                break
        return self.screenshot("server_selector_bottom_scrolled")

    def scroll_server_selector_to_top(self, *, swipe_count: int = 3) -> Path:
        self._record(
            {
                "type": "state",
                "state": "scroll_server_selector_to_top",
                "swipe_count": swipe_count,
            }
        )
        pull_count = min(max(1, swipe_count), 3)
        for index in range(pull_count):
            before = self.bot.screenshot_image()
            h, w = before.shape[:2]
            swipe_x = int(w * 0.125)
            start_y = int(h * 0.25)
            end_y = int(h * 0.58)
            list_top = int(h * 0.18)
            list_bottom = int(h * 0.62)
            roi_x1 = int(w * 0.03)
            roi_x2 = int(w * 0.94)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "server_selector_scroll_points",
                    "direction": "top",
                    "index": index,
                    "list_top": list_top,
                    "list_bottom": list_bottom,
                    "start_y": start_y,
                    "end_y": end_y,
                    "swipe_x": swipe_x,
                    "change_roi_x1": roi_x1,
                    "change_roi_x2": roi_x2,
                    "max_pulls": pull_count,
                }
            )

            self.bot.swipe(swipe_x, start_y, swipe_x, end_y, 380)
            self._sleep_with_watchdog(0.45, source="server_selector_scroll_top")
            after = self.bot.screenshot_image()
            change_score = self._roi_change_score(before, after, roi_x1, list_top, roi_x2, list_bottom)
            changed = change_score > 1.0
            self.screenshot(f"server_selector_top_swipe_{index:02d}_{'changed' if changed else 'static'}")
            self._record(
                {
                    "type": "state",
                    "state": "server_selector_swipe",
                    "direction": "top",
                    "index": index,
                    "changed": changed,
                    "used_x": swipe_x,
                    "change_score": round(change_score, 4),
                }
            )
            if not changed:
                break
        return self.screenshot("server_selector_top_scrolled")

    def click_enter_world_again_if_present(self, *, timeout_seconds: float = 1.2) -> bool:
        self._record({"type": "state", "state": "click_enter_world_again_if_present"})
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button = self.wait_for_template(
            "进入游戏前置-再争乱世按钮",
            "enter_world_again_button",
            timeout_seconds=timeout_seconds,
            threshold=0.74,
            region=(int(w * 0.30), int(h * 0.76), int(w * 0.42), int(h * 0.18)),
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "enter_world_again_button",
                "present": button is not None,
                "x": button.x if button else None,
                "y": button.y if button else None,
                "width": button.width if button else None,
                "height": button.height if button else None,
                "score": round(button.score, 4) if button else 0.0,
            }
        )
        if not button:
            return False

        point = Point(*button.center)
        self.tap("进入游戏前置-点击再争乱世", point, wait_seconds=8.0)
        self.skip_landscape_dialogs_if_present(max_taps=20, timeout_seconds=0.5)
        self.screenshot("after_click_enter_world_again")
        return True

    def detect_same_server_role_cards(
        self,
        image: np.ndarray,
    ) -> list[dict[str, int | float]]:
        h, w = image.shape[:2]
        if w >= h:
            return []

        # The same-server role picker places the selectable avatars in a narrow
        # band above the "进入征战" button. The selected card may include a glow,
        # so use a broad saturated component mask instead of a fixed-size crop.
        roi = (0, int(h * 0.58), w, int(h * 0.24))
        x, y, width, height = self._clip_region(image, roi)
        crop = image[y : y + height, x : x + width]
        if crop.size == 0:
            return []

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        mask = (
            ((hsv[:, :, 1] > 45) & (hsv[:, :, 2] > 60)).astype(np.uint8) * 255
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)

        cards: list[dict[str, int | float]] = []
        min_y = int(h * 0.60)
        max_y = int(h * 0.76)
        for index in range(1, count):
            local_x, local_y, card_w, card_h, area = [int(v) for v in stats[index]]
            center_x, center_y = centroids[index]
            global_x = x + local_x
            global_y = y + local_y
            if area < 800 or area > 26000:
                continue
            if card_w < 35 or card_h < 35 or card_w > 220 or card_h > 200:
                continue
            if not (min_y <= global_y <= max_y):
                continue

            cards.append(
                {
                    "x": global_x,
                    "y": global_y,
                    "width": card_w,
                    "height": card_h,
                    "area": area,
                    "center_x": round(float(x + center_x), 1),
                    "center_y": round(float(y + center_y), 1),
                }
            )

        cards.sort(key=lambda item: float(item["center_x"]))
        return cards

    def select_last_same_server_role_if_present(
        self,
        image: np.ndarray | None = None,
        *,
        wait_seconds: float = 0.8,
    ) -> bool:
        self._record({"type": "state", "state": "select_last_same_server_role_if_present"})
        if image is None:
            image = self.bot.screenshot_image()

        cards = self.detect_same_server_role_cards(image)
        present = len(cards) >= 2
        target = cards[-1] if present else None
        self._record(
            {
                "type": "vision_feature",
                "feature": "same_server_role_cards",
                "present": present,
                "count": len(cards),
                "cards": cards,
                "target_x": target["center_x"] if target else None,
                "target_y": target["center_y"] if target else None,
            }
        )
        if not target:
            return False

        self._save_image_snapshot("before_select_same_server_last_role", image)
        self._watchdog_reset()
        self.tap(
            "同区多角色-选择最后一个角色",
            Point(int(round(float(target["center_x"]))), int(round(float(target["center_y"])))),
            wait_seconds=wait_seconds,
        )
        self.screenshot("after_select_same_server_last_role")
        return True

    def click_role_enter_battle_if_present(self, *, timeout_seconds: float = 1.2) -> bool:
        self._record({"type": "state", "state": "click_role_enter_battle_if_present"})
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button = self.wait_for_template(
            "进入游戏前置-进入征战按钮",
            "role_enter_battle_button",
            timeout_seconds=timeout_seconds,
            threshold=0.74,
            region=(int(w * 0.36), int(h * 0.80), int(w * 0.30), int(h * 0.16)),
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "role_enter_battle_button",
                "present": button is not None,
                "x": button.x if button else None,
                "y": button.y if button else None,
                "width": button.width if button else None,
                "height": button.height if button else None,
                "score": round(button.score, 4) if button else 0.0,
            }
        )
        if not button:
            return False

        self.select_last_same_server_role_if_present(
            image,
            wait_seconds=self._fast_wait(0.8, 0.35),
        )
        point = Point(*button.center)
        self.tap("进入游戏前置-点击进入征战", point, wait_seconds=8.0)
        self.screenshot("after_click_role_enter_battle")
        return True

    def detect_season_bounty_start_in_image(self, image: np.ndarray) -> tuple[bool, dict, Point]:
        h, w = image.shape[:2]
        point = Point(int(w * 0.50), int(h * 0.75))
        metrics: dict = {
            "present": False,
            "reason": "landscape_screen" if w >= h else None,
            "tap_x": None,
            "tap_y": None,
        }
        if w >= h:
            return False, metrics, point

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        button_region = (int(w * 0.24), int(h * 0.70), int(w * 0.52), int(h * 0.13))
        banner_region = (int(w * 0.25), int(h * 0.17), int(w * 0.50), int(h * 0.35))
        date_region = (int(w * 0.10), int(h * 0.55), int(w * 0.80), int(h * 0.10))

        bx, by, bw, bh = self._clip_region(image, button_region)
        button_gray = gray[by : by + bh, bx : bx + bw]
        button_hsv = hsv[by : by + bh, bx : bx + bw]
        button_bright_ratio = float((button_gray > 175).mean()) if button_gray.size else 0.0
        button_very_bright_ratio = float((button_gray > 215).mean()) if button_gray.size else 0.0
        button_gold_ratio = float(
            (
                (button_hsv[:, :, 0] > 10)
                & (button_hsv[:, :, 0] < 35)
                & (button_hsv[:, :, 1] > 40)
                & (button_hsv[:, :, 2] > 110)
            ).mean()
        ) if button_hsv.size else 0.0

        fx, fy, fw, fh = self._clip_region(image, banner_region)
        banner_gray = gray[fy : fy + fh, fx : fx + fw]
        banner_hsv = hsv[fy : fy + fh, fx : fx + fw]
        banner_dark_ratio = float((banner_gray < 70).mean()) if banner_gray.size else 0.0
        banner_low_sat_ratio = float((banner_hsv[:, :, 1] < 80).mean()) if banner_hsv.size else 0.0
        banner_gold_ratio = float(
            (
                (banner_hsv[:, :, 0] > 10)
                & (banner_hsv[:, :, 0] < 35)
                & (banner_hsv[:, :, 1] > 40)
                & (banner_hsv[:, :, 2] > 110)
            ).mean()
        ) if banner_hsv.size else 0.0

        dx, dy, dw, dh = self._clip_region(image, date_region)
        date_gray = gray[dy : dy + dh, dx : dx + dw]
        date_bright_ratio = float((date_gray > 175).mean()) if date_gray.size else 0.0
        date_edge_ratio = float(cv2.Canny(date_gray, 60, 140).mean() / 255) if date_gray.size else 0.0

        present = (
            button_bright_ratio >= 0.15
            and button_very_bright_ratio >= 0.055
            and button_gold_ratio >= 0.035
            and banner_dark_ratio >= 0.26
            and banner_low_sat_ratio >= 0.70
            and banner_gold_ratio <= 0.12
            and (date_bright_ratio >= 0.18 or date_edge_ratio >= 0.09)
        )
        metrics = {
            "present": present,
            "button_bright_ratio": round(button_bright_ratio, 4),
            "button_very_bright_ratio": round(button_very_bright_ratio, 4),
            "button_gold_ratio": round(button_gold_ratio, 4),
            "banner_dark_ratio": round(banner_dark_ratio, 4),
            "banner_low_sat_ratio": round(banner_low_sat_ratio, 4),
            "banner_gold_ratio": round(banner_gold_ratio, 4),
            "date_bright_ratio": round(date_bright_ratio, 4),
            "date_edge_ratio": round(date_edge_ratio, 4),
            "tap_x": point.x if present else None,
            "tap_y": point.y if present else None,
        }
        return present, metrics, point

    def click_season_bounty_start_if_present(self, *, timeout_seconds: float = 1.0) -> bool:
        self._record({"type": "state", "state": "click_season_bounty_start_if_present"})
        end_at = time() + max(0.1, timeout_seconds)
        last_metrics: dict | None = None
        while time() < end_at:
            image = self.bot.screenshot_image()
            present, metrics, point = self.detect_season_bounty_start_in_image(image)
            last_metrics = metrics
            if present:
                self._save_image_snapshot("before_click_season_bounty_start", image)
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "season_bounty_start_button",
                        **metrics,
                    }
                )
                self._watchdog_reset()
                self.tap("进入游戏前置-赏金赛开始征战", point, wait_seconds=4.0)
                self.screenshot("after_click_season_bounty_start")
                return True
            self._sleep_with_watchdog(0.2, source="click_season_bounty_start_if_present")

        if last_metrics is not None:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "season_bounty_start_button",
                    **last_metrics,
                }
            )
        return False

    def find_pale_prompt_buttons_in_image(self, image: np.ndarray) -> list[dict]:
        h, w = image.shape[:2]
        x, y, width, height = self._clip_region(
            image,
            (int(w * 0.18), int(h * 0.54), int(w * 0.64), int(h * 0.12)),
        )
        crop = image[y : y + height, x : x + width]
        if crop.size == 0:
            return []
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        mask = (((hsv[:, :, 1] < 85) & (hsv[:, :, 2] > 135) & (gray > 120)).astype("uint8")) * 255
        kernel = np.ones((5, 9), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        buttons = []
        for contour in contours:
            area = float(cv2.contourArea(contour))
            bx, by, bw, bh = cv2.boundingRect(contour)
            if area < 700 or bw < 45 or bh < 20:
                continue
            buttons.append(
                {
                    "x": int(x + bx),
                    "y": int(y + by),
                    "width": int(bw),
                    "height": int(bh),
                    "area": round(area, 1),
                    "center_x": int(x + bx + bw / 2),
                    "center_y": int(y + by + bh / 2),
                }
            )
        return sorted(buttons, key=lambda item: item["x"])

    def detect_inactive_reselect_prompt_in_image(
        self,
        image: np.ndarray,
        *,
        threshold: float = 0.66,
    ) -> tuple[bool, dict, Point]:
        h, w = image.shape[:2]
        point = Point(int(w * 0.50), int(h * 0.592))
        title_region = (int(w * 0.28), int(h * 0.36), int(w * 0.44), int(h * 0.12))
        button_region = (int(w * 0.34), int(h * 0.54), int(w * 0.32), int(h * 0.12))
        title = self._find_template_in_image(
            image,
            "inactive_reselect_prompt_title",
            threshold=threshold,
            region=title_region,
        )
        button = self._find_template_in_image(
            image,
            "inactive_reselect_confirm_button",
            threshold=0.62,
            region=button_region,
        )
        if button:
            point = Point(*button.center)
        prompt_buttons = self.find_pale_prompt_buttons_in_image(image)
        if not button and len(prompt_buttons) == 1:
            only_button = prompt_buttons[0]
            point = Point(int(only_button["center_x"]), int(only_button["center_y"]))

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        px, py, pw, ph = self._clip_region(
            image,
            (int(w * 0.12), int(h * 0.37), int(w * 0.76), int(h * 0.28)),
        )
        tx, ty, tw, th = self._clip_region(
            image,
            (int(w * 0.35), int(h * 0.39), int(w * 0.30), int(h * 0.06)),
        )
        bx, by, bw, bh = self._clip_region(image, button_region)
        panel_gray = gray[py : py + ph, px : px + pw]
        title_gray = gray[ty : ty + th, tx : tx + tw]
        title_hsv = hsv[ty : ty + th, tx : tx + tw]
        button_gray = gray[by : by + bh, bx : bx + bw]
        button_hsv = hsv[by : by + bh, bx : bx + bw]

        panel_dark_ratio = float((panel_gray < 80).mean()) if panel_gray.size else 0.0
        full_dark_ratio = float((gray < 80).mean()) if gray.size else 0.0
        title_bright_ratio = float((title_gray > 160).mean()) if title_gray.size else 0.0
        title_gold_ratio = (
            float(
                (
                    (title_hsv[:, :, 0] > 10)
                    & (title_hsv[:, :, 0] < 40)
                    & (title_hsv[:, :, 1] > 40)
                    & (title_hsv[:, :, 2] > 100)
                ).mean()
            )
            if title_hsv.size
            else 0.0
        )
        button_bright_ratio = float((button_gray > 160).mean()) if button_gray.size else 0.0
        button_white_ratio = (
            float(((button_hsv[:, :, 1] < 65) & (button_hsv[:, :, 2] > 150)).mean())
            if button_hsv.size
            else 0.0
        )
        single_button_prompt = len(prompt_buttons) == 1
        visual_present = (
            single_button_prompt
            and
            panel_dark_ratio >= 0.82
            and full_dark_ratio >= 0.78
            and button_bright_ratio >= 0.18
            and button_white_ratio >= 0.22
            and title_bright_ratio <= 0.12
            and title_gold_ratio <= 0.10
        )
        present = (title is not None and single_button_prompt) or visual_present
        metrics = {
            "present": present,
            "source": (
                "title_template"
                if title and single_button_prompt
                else ("visual_fallback" if visual_present else "button_count_reject" if title else "none")
            ),
            "x": title.x if title else None,
            "y": title.y if title else None,
            "width": title.width if title else None,
            "height": title.height if title else None,
            "score": round(title.score, 4) if title else 0.0,
            "button_present": button is not None,
            "prompt_button_count": len(prompt_buttons),
            "prompt_buttons": prompt_buttons,
            "button_x": button.x if button else None,
            "button_y": button.y if button else None,
            "button_score": round(button.score, 4) if button else 0.0,
            "panel_dark_ratio": round(panel_dark_ratio, 4),
            "full_dark_ratio": round(full_dark_ratio, 4),
            "title_bright_ratio": round(title_bright_ratio, 4),
            "title_gold_ratio": round(title_gold_ratio, 4),
            "button_bright_ratio": round(button_bright_ratio, 4),
            "button_white_ratio": round(button_white_ratio, 4),
            "tap_x": point.x if present else None,
            "tap_y": point.y if present else None,
        }
        return present, metrics, point

    def confirm_inactive_reselect_region_if_present(self, *, timeout_seconds: float = 1.2) -> bool:
        self._record({"type": "state", "state": "confirm_inactive_reselect_region_if_present"})
        end_at = time() + max(0.1, timeout_seconds)
        last_metrics: dict | None = None
        while time() < end_at:
            image = self.bot.screenshot_image()
            present, metrics, point = self.detect_inactive_reselect_prompt_in_image(image)
            last_metrics = metrics
            if present:
                self._save_image_snapshot("before_confirm_inactive_reselect_region", image)
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "inactive_reselect_region_prompt",
                        **metrics,
                    }
                )
                self._watchdog_reset()
                self.tap("重新选州提示-点击确定", point, wait_seconds=3.0)
                self.screenshot("after_confirm_inactive_reselect_region")
                return True
            self._sleep_with_watchdog(0.2, source="confirm_inactive_reselect_region_if_present")

        if last_metrics is not None:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "inactive_reselect_region_prompt",
                    **last_metrics,
                }
            )
        return False

    def confirm_account_logout_if_present(self, *, timeout_seconds: float = 1.2) -> bool:
        self._record({"type": "state", "state": "confirm_account_logout_if_present"})
        end_at = time() + max(0.1, timeout_seconds)
        last_record: dict | None = None
        while time() < end_at:
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]
            title = self._find_template_in_image(
                image,
                "inactive_reselect_prompt_title",
                threshold=0.66,
                region=(int(w * 0.28), int(h * 0.34), int(w * 0.44), int(h * 0.16)),
            )
            buttons = self.find_pale_prompt_buttons_in_image(image)
            present = title is not None and len(buttons) >= 2
            last_record = {
                "type": "vision_feature",
                "feature": "account_logout_confirm_prompt",
                "present": present,
                "title_x": title.x if title else None,
                "title_y": title.y if title else None,
                "title_width": title.width if title else None,
                "title_height": title.height if title else None,
                "title_score": round(title.score, 4) if title else 0.0,
                "button_count": len(buttons),
                "buttons": buttons,
            }
            if present:
                left_button = buttons[0]
                point = Point(int(left_button["center_x"]), int(left_button["center_y"]))
                last_record["tap_x"] = point.x
                last_record["tap_y"] = point.y
                self._save_image_snapshot("before_confirm_account_logout", image)
                self._record(last_record)
                self._watchdog_reset()
                self.tap("切换账号流程-确认登出当前账号", point, wait_seconds=3.0)
                self.screenshot("after_confirm_account_logout")
                return True
            self._sleep_with_watchdog(0.2, source="confirm_account_logout_if_present")

        if last_record is not None:
            self._record(last_record)
        return False

    def select_default_region_if_present(self, *, timeout_seconds: float = 1.2) -> bool:
        self._record({"type": "state", "state": "select_default_region_if_present"})
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        confirm_candidates = (
            ("region_confirm_label", (int(w * 0.16), int(h * 0.54), int(w * 0.62), int(h * 0.20)), 0.72),
            ("region_confirm_button", (int(w * 0.20), int(h * 0.52), int(w * 0.50), int(h * 0.24)), 0.74),
        )

        def find_region_confirm(label: str, wait_seconds: float) -> tuple[str | None, Match | None]:
            for candidate_key, candidate_region, candidate_threshold in confirm_candidates:
                found = self.wait_for_template(
                    label,
                    candidate_key,
                    timeout_seconds=wait_seconds,
                    threshold=candidate_threshold,
                    region=candidate_region,
                )
                if found:
                    return candidate_key, found
            return None, None

        def visual_region_confirm_point(label: str) -> Point | None:
            current = self.bot.screenshot_image()
            current_h, current_w = current.shape[:2]
            if current_w > current_h:
                button_region = (
                    int(current_w * 0.34),
                    int(current_h * 0.58),
                    int(current_w * 0.20),
                    int(current_h * 0.16),
                )
                panel_region = (
                    int(current_w * 0.24),
                    int(current_h * 0.28),
                    int(current_w * 0.52),
                    int(current_h * 0.44),
                )
                point = Point(int(current_w * 0.42), int(current_h * 0.66))
            else:
                button_region = (
                    int(current_w * 0.22),
                    int(current_h * 0.54),
                    int(current_w * 0.38),
                    int(current_h * 0.15),
                )
                panel_region = (
                    int(current_w * 0.08),
                    int(current_h * 0.38),
                    int(current_w * 0.84),
                    int(current_h * 0.30),
                )
                point = Point(int(current_w * 0.35), int(current_h * 0.59))

            button_crop = self._crop(current, button_region)
            panel_crop = self._crop(current, panel_region)
            button_gray = cv2.cvtColor(button_crop, cv2.COLOR_BGR2GRAY)
            panel_gray = cv2.cvtColor(panel_crop, cv2.COLOR_BGR2GRAY)
            bright_ratio = float((button_gray > 145).mean())
            panel_dark_ratio = float((panel_gray < 90).mean())
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "region_confirm_visual_fallback",
                    "label": label,
                    "bright_ratio": round(bright_ratio, 3),
                    "panel_dark_ratio": round(panel_dark_ratio, 3),
                    "region_x": button_region[0],
                    "region_y": button_region[1],
                    "region_width": button_region[2],
                    "region_height": button_region[3],
                    "tap_x": point.x,
                    "tap_y": point.y,
                }
            )
            if bright_ratio >= 0.08 and panel_dark_ratio >= 0.12:
                return point
            return None

        def tap_region_confirm(label: str, point: Point, *, wait_after: float = 8.0) -> None:
            self.tap(label, point, wait_seconds=1.2)

            retry_point: Point | None = None
            retry_source = "missing"
            retry_key, retry_match = find_region_confirm(f"{label}-点击后复查", 0.35)
            if retry_match:
                retry_point = Point(*retry_match.center)
                retry_source = retry_key or "template_after_tap"
            else:
                visual_retry = visual_region_confirm_point(f"{label}-点击后视觉复查")
                if visual_retry:
                    retry_point = visual_retry
                    retry_source = "visual_after_tap"

            self._record(
                {
                    "type": "vision_feature",
                    "feature": "region_confirm_after_tap",
                    "present": retry_point is not None,
                    "source": retry_source,
                    "tap_x": retry_point.x if retry_point else None,
                    "tap_y": retry_point.y if retry_point else None,
                }
            )
            if retry_point:
                self.tap(f"{label}-复点", retry_point, wait_seconds=wait_after)
            elif wait_after > 1.2:
                self._sleep_with_watchdog(wait_after - 1.2, source=label)

        def enter_regions() -> tuple[tuple[int, int, int, int], ...]:
            if w > h:
                return (
                    (int(w * 0.68), int(h * 0.80), int(w * 0.30), int(h * 0.18)),
                    (int(w * 0.68), int(h * 0.66), int(w * 0.30), int(h * 0.18)),
                )
            return ((int(w * 0.25), int(h * 0.86), int(w * 0.50), int(h * 0.12)),)

        def find_region_enter(label: str, wait_seconds: float) -> tuple[Match | None, Point | None, str, tuple[int, int, int, int]]:
            for candidate_region in enter_regions():
                enter = self.wait_for_template(
                    f"{label}-文字",
                    "region_enter_label",
                    timeout_seconds=wait_seconds,
                    threshold=0.72,
                    region=candidate_region,
                )
                if enter:
                    if w > h:
                        point = Point(enter.x + int(enter.width * 0.88), enter.y + int(enter.height * 0.45))
                    else:
                        point = Point(
                            int(w * 0.50),
                            max(
                                int(h * 0.90),
                                min(int(h * 0.98), enter.y + int(enter.height * 0.65)),
                            ),
                        )
                    return enter, point, "label_template", candidate_region

                enter = self.wait_for_template(
                    f"{label}-按钮",
                    "region_enter_selected_button",
                    timeout_seconds=0.25,
                    threshold=0.72,
                    region=candidate_region,
                )
                if enter:
                    return enter, Point(*enter.center), "button_template", candidate_region
            return None, None, "missing", enter_regions()[0]

        confirm_key, confirm = find_region_confirm("选州前置-确认入驻-优先检测", 0.4)
        if confirm:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "region_confirm_button",
                    "present": True,
                    "source": "pre_existing_confirm",
                    "template": confirm_key,
                    "x": confirm.x,
                    "y": confirm.y,
                    "width": confirm.width,
                    "height": confirm.height,
                    "score": round(confirm.score, 4),
                }
            )
            tap_region_confirm("选州前置-确认默认入驻", Point(*confirm.center))
            self.screenshot("after_click_default_region_confirm")
            return True

        enter_button, enter_point, enter_source, enter_region = find_region_enter("选州前置-入驻按钮-无标题检测", 0.45)
        if enter_button and enter_point:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "region_enter_selected_button",
                    "present": True,
                    "source": f"{enter_source}_without_title",
                    "region_x": enter_region[0],
                    "region_y": enter_region[1],
                    "region_width": enter_region[2],
                    "region_height": enter_region[3],
                    "x": enter_button.x,
                    "y": enter_button.y,
                    "width": enter_button.width,
                    "height": enter_button.height,
                    "score": round(enter_button.score, 4),
                    "tap_x": enter_point.x,
                    "tap_y": enter_point.y,
                }
            )
            self.tap("选州前置-点击默认入驻", enter_point, wait_seconds=2.0)
            confirm_key, confirm = find_region_confirm("选州前置-确认入驻", 2.0)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "region_confirm_button",
                    "present": confirm is not None,
                    "template": confirm_key,
                    "x": confirm.x if confirm else None,
                    "y": confirm.y if confirm else None,
                    "width": confirm.width if confirm else None,
                    "height": confirm.height if confirm else None,
                    "score": round(confirm.score, 4) if confirm else 0.0,
                }
            )
            if confirm:
                tap_region_confirm("选州前置-确认默认入驻", Point(*confirm.center))
            elif w > h:
                fallback_confirm = visual_region_confirm_point("选州前置-确认入驻-横屏视觉兜底")
                if fallback_confirm is None:
                    fallback_confirm = Point(int(w * 0.42), int(h * 0.66))
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "region_confirm_button",
                        "present": False,
                        "source": "landscape_fallback_after_enter",
                        "tap_x": fallback_confirm.x,
                        "tap_y": fallback_confirm.y,
                    }
                )
                tap_region_confirm("选州前置-确认默认入驻-横屏备用坐标", fallback_confirm)
            else:
                self._record(
                    {
                        "type": "state",
                        "state": "region_enter_no_confirm_after_tap_portrait",
                        "tap_x": enter_point.x,
                        "tap_y": enter_point.y,
                        "sample_label": "after_click_default_region",
                    }
                )
            self.screenshot("after_click_default_region")
            return True

        title = None
        title_key = None
        for candidate_key, candidate_region in (
            ("region_select_title_top", (int(w * 0.24), 0, int(w * 0.52), int(h * 0.08))),
            ("region_select_title", (int(w * 0.34), 0, int(w * 0.34), int(h * 0.12))),
        ):
            title = self.wait_for_template(
                "选州前置-选择起兵之地",
                candidate_key,
                timeout_seconds=timeout_seconds,
                threshold=0.72,
                region=candidate_region,
            )
            if title:
                title_key = candidate_key
                break
        self._record(
            {
                "type": "vision_feature",
                "feature": "region_select_title",
                "present": title is not None,
                "template": title_key,
                "x": title.x if title else None,
                "y": title.y if title else None,
                "width": title.width if title else None,
                "height": title.height if title else None,
                "score": round(title.score, 4) if title else 0.0,
            }
        )
        if not title:
            return False

        enter_button, enter_point, button_source, enter_region = find_region_enter("选州前置-底部入驻", 0.8)
        if not enter_button or not enter_point:
            confirm_point = visual_region_confirm_point("选州前置-标题页已有确认弹窗")
            if confirm_point:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "region_confirm_button",
                        "present": True,
                        "source": "visual_existing_confirm_on_region_page",
                        "tap_x": confirm_point.x,
                        "tap_y": confirm_point.y,
                    }
                )
                tap_region_confirm("选州前置-确认默认入驻-已有弹窗", confirm_point)
                self.screenshot("after_click_default_region_confirm")
                return True

        enter_button, enter_point, button_source, enter_region = find_region_enter("选州前置-底部入驻", 0.8)
        if enter_button and enter_point:
            point = enter_point
            button_score = round(enter_button.score, 4)
        else:
            if w > h:
                point = Point(int(w * 0.84), int(h * 0.90))
            else:
                point = Point(int(w * 0.50), int(h * 0.955))
            button_source = "fallback"
            button_score = 0.0
        self._record(
            {
                "type": "vision_feature",
                "feature": "region_enter_selected_button",
                "present": enter_button is not None,
                "source": button_source,
                "region_x": enter_region[0],
                "region_y": enter_region[1],
                "region_width": enter_region[2],
                "region_height": enter_region[3],
                "x": enter_button.x if enter_button else point.x,
                "y": enter_button.y if enter_button else point.y,
                "width": enter_button.width if enter_button else None,
                "height": enter_button.height if enter_button else None,
                "score": button_score,
                "tap_x": point.x,
            "tap_y": point.y,
            }
        )
        self.tap("选州前置-点击默认入驻", point, wait_seconds=2.0)
        confirm_key, confirm = find_region_confirm("选州前置-确认入驻", 2.0)
        self._record(
            {
                "type": "vision_feature",
                "feature": "region_confirm_button",
                "present": confirm is not None,
                "template": confirm_key,
                "x": confirm.x if confirm else None,
                "y": confirm.y if confirm else None,
                "width": confirm.width if confirm else None,
                "height": confirm.height if confirm else None,
                "score": round(confirm.score, 4) if confirm else 0.0,
            }
        )
        if confirm:
            tap_region_confirm("选州前置-确认默认入驻", Point(*confirm.center))
        elif w > h:
            fallback_confirm = visual_region_confirm_point("选州前置-确认入驻-横屏视觉兜底")
            if fallback_confirm is None:
                fallback_confirm = Point(int(w * 0.42), int(h * 0.66))
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "region_confirm_button",
                    "present": False,
                    "source": "landscape_fallback_after_enter",
                    "tap_x": fallback_confirm.x,
                    "tap_y": fallback_confirm.y,
                }
            )
            tap_region_confirm("选州前置-确认默认入驻-横屏备用坐标", fallback_confirm)
        else:
            self._record(
                {
                    "type": "state",
                    "state": "region_enter_no_confirm_after_tap_portrait",
                    "tap_x": point.x,
                    "tap_y": point.y,
                    "sample_label": "after_click_default_region",
                }
            )
        self.screenshot("after_click_default_region")
        return True

    def click_general_reward_card_if_present(self) -> bool:
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            return False

        top = image[: int(h * 0.25), :]
        bottom = image[int(h * 0.78) : int(h * 0.98), :]
        bg_pixels = np.vstack([top.reshape(-1, 3), bottom.reshape(-1, 3)])
        bg_gray = cv2.cvtColor(bg_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY).reshape(-1)

        card = image[int(h * 0.37) : int(h * 0.63), int(w * 0.35) : int(w * 0.65)]
        card_gray = cv2.cvtColor(card, cv2.COLOR_BGR2GRAY)
        card_hsv = cv2.cvtColor(card, cv2.COLOR_BGR2HSV)
        edge_ratio = float(cv2.Canny(card_gray, 60, 120).mean()) / 255.0
        bg_dark_ratio = float((bg_gray < 70).mean())
        card_bright_ratio = float((card_gray > 120).mean())
        card_saturation_ratio = float((card_hsv[:, :, 1] > 70).mean())
        present = (
            bg_dark_ratio >= 0.90
            and card_bright_ratio >= 0.24
            and card_saturation_ratio >= 0.55
            and edge_ratio >= 0.12
        )
        point = Point(int(w * 0.50), int(h * 0.74))
        self._record(
            {
                "type": "vision_feature",
                "feature": "general_reward_card_overlay",
                "present": present,
                "bg_dark_ratio": round(bg_dark_ratio, 4),
                "card_bright_ratio": round(card_bright_ratio, 4),
                "card_saturation_ratio": round(card_saturation_ratio, 4),
                "edge_ratio": round(edge_ratio, 4),
                "tap_x": point.x if present else None,
                "tap_y": point.y if present else None,
            }
        )
        if not present:
            return False

        self._save_image_snapshot("before_click_general_reward_card", image)
        self._watchdog_reset()
        self.tap("进入游戏前置-跳过获得武将奖励", point, wait_seconds=1.0)
        self.tap("进入游戏前置-跳过获得武将奖励-复点", point, wait_seconds=1.2)
        self.screenshot("after_click_general_reward_card")
        return True

    def click_returning_player_enter_game_if_present(self, image: np.ndarray | None = None) -> bool:
        self._record({"type": "state", "state": "click_returning_player_enter_game_if_present"})
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "returning_player_enter_game",
                    "present": False,
                    "reason": "landscape_orientation",
                }
            )
            return False

        title_x, title_y, title_w, title_h = self._clip_region(
            image,
            (int(w * 0.28), int(h * 0.03), int(w * 0.45), int(h * 0.08)),
        )
        button_x, button_y, button_w, button_h = self._clip_region(
            image,
            (int(w * 0.68), int(h * 0.42), int(w * 0.29), int(h * 0.08)),
        )
        title = image[title_y : title_y + title_h, title_x : title_x + title_w]
        button = image[button_y : button_y + button_h, button_x : button_x + button_w]
        title_hsv = cv2.cvtColor(title, cv2.COLOR_BGR2HSV)
        button_hsv = cv2.cvtColor(button, cv2.COLOR_BGR2HSV)
        title_hue, title_sat, title_val = cv2.split(title_hsv)
        button_hue, button_sat, button_val = cv2.split(button_hsv)
        title_gold_ratio = float(
            (((title_hue >= 15) & (title_hue <= 42) & (title_sat > 45) & (title_val > 95))).mean()
        )
        title_bright_ratio = float((cv2.cvtColor(title, cv2.COLOR_BGR2GRAY) > 150).mean())
        button_orange_ratio = float(
            (((button_hue >= 5) & (button_hue <= 30) & (button_sat > 65) & (button_val > 65))).mean()
        )
        button_dark_ratio = float(((button_val < 75) & (button_sat > 20)).mean())
        present = (
            title_gold_ratio >= 0.18
            and title_bright_ratio >= 0.18
            and button_orange_ratio >= 0.12
            and button_dark_ratio >= 0.18
        )
        point = Point(button_x + button_w // 2, button_y + button_h // 2)
        self._record(
            {
                "type": "vision_feature",
                "feature": "returning_player_enter_game",
                "present": present,
                "title_gold_ratio": round(title_gold_ratio, 4),
                "title_bright_ratio": round(title_bright_ratio, 4),
                "button_orange_ratio": round(button_orange_ratio, 4),
                "button_dark_ratio": round(button_dark_ratio, 4),
                "tap_x": point.x if present else None,
                "tap_y": point.y if present else None,
            }
        )
        if not present:
            return False
        self._save_image_snapshot("before_click_returning_player_enter_game", image)
        self.tap("进入游戏前置-迎主回归进入游戏", point, wait_seconds=self._fast_wait(4.0, 2.4))
        self.screenshot("after_click_returning_player_enter_game")
        return True

    def close_notice_ack_if_present(self, image: np.ndarray | None = None) -> bool:
        self._record({"type": "state", "state": "close_notice_ack_if_present"})
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "notice_ack_button",
                    "present": False,
                    "reason": "landscape_orientation",
                }
            )
            return False

        panel_x, panel_y, panel_w, panel_h = self._clip_region(
            image,
            (int(w * 0.03), int(h * 0.10), int(w * 0.94), int(h * 0.80)),
        )
        button_x, button_y, button_w, button_h = self._clip_region(
            image,
            (int(w * 0.39), int(h * 0.84), int(w * 0.22), int(h * 0.07)),
        )
        panel = image[panel_y : panel_y + panel_h, panel_x : panel_x + panel_w]
        button = image[button_y : button_y + button_h, button_x : button_x + button_w]
        panel_gray = cv2.cvtColor(panel, cv2.COLOR_BGR2GRAY)
        button_gray = cv2.cvtColor(button, cv2.COLOR_BGR2GRAY)
        button_hsv = cv2.cvtColor(button, cv2.COLOR_BGR2HSV)
        _, button_sat, button_val = cv2.split(button_hsv)
        panel_dark_ratio = float((panel_gray < 70).mean())
        panel_edge_ratio = float((cv2.Canny(panel_gray, 60, 140) > 0).mean())
        button_pale_ratio = float(((button_sat < 55) & (button_val > 105)).mean())
        button_bright_ratio = float((button_gray > 135).mean())
        button_edge_ratio = float((cv2.Canny(button_gray, 60, 140) > 0).mean())
        present = (
            panel_dark_ratio >= 0.72
            and panel_edge_ratio >= 0.04
            and button_pale_ratio >= 0.22
            and button_bright_ratio >= 0.18
            and button_edge_ratio >= 0.04
        ) or (
            panel_dark_ratio >= 0.90
            and panel_edge_ratio >= 0.025
            and button_pale_ratio >= 0.30
            and button_bright_ratio >= 0.25
            and button_edge_ratio >= 0.08
        )
        point = Point(button_x + button_w // 2, button_y + button_h // 2)
        self._record(
            {
                "type": "vision_feature",
                "feature": "notice_ack_button",
                "present": present,
                "panel_dark_ratio": round(panel_dark_ratio, 4),
                "panel_edge_ratio": round(panel_edge_ratio, 4),
                "button_pale_ratio": round(button_pale_ratio, 4),
                "button_bright_ratio": round(button_bright_ratio, 4),
                "button_edge_ratio": round(button_edge_ratio, 4),
                "tap_x": point.x if present else None,
                "tap_y": point.y if present else None,
            }
        )
        if not present:
            return False
        self._save_image_snapshot("before_close_notice_ack", image)
        self.tap("进入游戏前置-关闭公告我知道了", point, wait_seconds=self._fast_wait(1.4, 0.8))
        self.screenshot("after_close_notice_ack")
        return True

    def close_xiaomi_quick_login_prompt_if_present(self, *, timeout_seconds: float = 0.8) -> bool:
        if self.client_name != "小米":
            return False
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            return False
        match = self.wait_for_template(
            "小米客户端-快速登录提示-暂不开启",
            "xiaomi_quick_login_decline_button",
            timeout_seconds=timeout_seconds,
            threshold=0.92,
            region=(int(w * 0.48), int(h * 0.52), int(w * 0.30), int(h * 0.14)),
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "xiaomi_quick_login_prompt",
                "present": match is not None,
                "x": match.x if match else None,
                "y": match.y if match else None,
                "width": match.width if match else None,
                "height": match.height if match else None,
                "score": round(match.score, 4) if match else 0.0,
            }
        )
        if not match:
            return False
        self._save_image_snapshot("before_close_xiaomi_quick_login_prompt", image)
        self.tap("小米客户端-快速登录提示-暂不开启", Point(*match.center), wait_seconds=3.0)
        self._watchdog_reset()
        self.screenshot("after_close_xiaomi_quick_login_prompt")
        return True

    def confirm_xiaomi_missing_resources_if_present(self, *, timeout_seconds: float = 0.8) -> bool:
        if self.client_name != "小米":
            return False
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            return False
        match = self.wait_for_template(
            "小米客户端-补充资源下载-确定",
            "xiaomi_missing_resources_confirm_button",
            timeout_seconds=timeout_seconds,
            threshold=0.90,
            region=(int(w * 0.16), int(h * 0.54), int(w * 0.34), int(h * 0.16)),
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "xiaomi_missing_resources_prompt",
                "present": match is not None,
                "x": match.x if match else None,
                "y": match.y if match else None,
                "width": match.width if match else None,
                "height": match.height if match else None,
                "score": round(match.score, 4) if match else 0.0,
            }
        )
        if not match:
            return False
        self._save_image_snapshot("before_confirm_xiaomi_missing_resources", image)
        self.tap("小米客户端-补充资源下载-确定", Point(*match.center), wait_seconds=8.0)
        self._watchdog_reset()
        self.screenshot("after_confirm_xiaomi_missing_resources")
        return True

    def save_xiaomi_graphics_settings_if_present(self, *, timeout_seconds: float = 0.8) -> bool:
        if self.client_name != "小米":
            return False
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            return False
        match = self.wait_for_template(
            "小米客户端-画面设置-保存",
            "xiaomi_graphics_settings_save_button",
            timeout_seconds=timeout_seconds,
            threshold=0.78,
            region=(int(w * 0.42), int(h * 0.66), int(w * 0.34), int(h * 0.14)),
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "xiaomi_graphics_settings",
                "present": match is not None,
                "x": match.x if match else None,
                "y": match.y if match else None,
                "width": match.width if match else None,
                "height": match.height if match else None,
                "score": round(match.score, 4) if match else 0.0,
            }
        )
        if not match:
            return False
        self._save_image_snapshot("before_save_xiaomi_graphics_settings", image)
        self.tap("小米客户端-画面设置-保存", Point(*match.center), wait_seconds=3.0)
        self._watchdog_reset()
        self.screenshot("after_save_xiaomi_graphics_settings")
        return True

    def confirm_xiaomi_background_resources_if_present(self) -> bool:
        if self.client_name != "小米":
            return False
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            return False
        match = self._find_template_in_image(
            image,
            "xiaomi_background_resources_confirm_button",
            threshold=0.90,
            region=(int(w * 0.16), int(h * 0.52), int(w * 0.34), int(h * 0.16)),
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "xiaomi_background_resources_prompt",
                "present": match is not None,
                "x": match.x if match else None,
                "y": match.y if match else None,
                "width": match.width if match else None,
                "height": match.height if match else None,
                "score": round(match.score, 4) if match else 0.0,
            }
        )
        if not match:
            return False
        self._save_image_snapshot("before_confirm_xiaomi_background_resources", image)
        self.tap("小米客户端-静默下载资源-确认", Point(*match.center), wait_seconds=3.0)
        self._watchdog_reset()
        self.screenshot("after_confirm_xiaomi_background_resources")
        return True

    def handle_entry_preconditions(
        self,
        *,
        max_rounds: int = 6,
        click_login_prompts: bool = True,
    ) -> bool:
        self._record(
            {
                "type": "state",
                "state": "handle_entry_preconditions",
                "max_rounds": max_rounds,
                "click_login_prompts": click_login_prompts,
            }
        )
        handled_any = False
        for index in range(max(1, max_rounds)):
            self._record(
                {
                    "type": "state",
                    "state": "entry_preconditions_round",
                    "round": index + 1,
                    "max_rounds": max_rounds,
                }
            )
            if self.click_general_reward_card_if_present():
                handled_any = True
                continue
            if self.confirm_xiaomi_missing_resources_if_present():
                handled_any = True
                continue
            if self.confirm_xiaomi_background_resources_if_present():
                handled_any = True
                continue
            if self.close_xiaomi_quick_login_prompt_if_present():
                handled_any = True
                continue
            if self.save_xiaomi_graphics_settings_if_present():
                handled_any = True
                continue
            if self.close_notice_ack_if_present():
                handled_any = True
                continue
            if click_login_prompts:
                if self.click_recent_login_account_if_present(timeout_seconds=0.35):
                    handled_any = True
                    continue
                if self.click_account_login_modal_if_present(timeout_seconds=0.35):
                    handled_any = True
                    continue
            elif self.detect_account_login_surface(timeout_seconds=0.25):
                self._record(
                    {
                        "type": "state",
                        "state": "entry_preconditions_done",
                        "reason": "account_login_surface_ready",
                        "round": index + 1,
                    }
                )
                break
            if self.confirm_inactive_reselect_region_if_present(timeout_seconds=self._fast_timeout(0.8, 0.25)):
                handled_any = True
                continue
            if self.select_default_region_if_present(timeout_seconds=self._fast_timeout(1.2, 0.55)):
                handled_any = True
                continue
            if self.skip_landscape_dialogs_if_present(max_taps=20, timeout_seconds=self._fast_timeout(0.5, 0.30)):
                handled_any = True
                continue
            if self.skip_portrait_dialogs_if_present(max_taps=30, timeout_seconds=self._fast_timeout(0.5, 0.30)):
                handled_any = True
                continue
            if self.close_known_retreat_if_present(timeout_seconds=self._fast_timeout(0.8, 0.25)):
                handled_any = True
                continue
            if self.close_signin_reward_if_present(timeout_seconds=self._fast_timeout(0.8, 0.25)):
                handled_any = True
                continue
            if self.close_orange_card_detail_if_present(timeout_seconds=self._fast_timeout(0.9, 0.35)):
                handled_any = True
                continue
            if self.detect_like_main_screen():
                self._record(
                    {
                        "type": "state",
                        "state": "entry_preconditions_done",
                        "reason": "main_screen_detected",
                        "round": index + 1,
                    }
                )
                break

            if self.close_exit_confirm_if_present(timeout_seconds=0.35):
                handled_any = True
                continue
            if self.click_title_enter_if_present(
                timeout_seconds=0.45,
                click_login_after_prompt=click_login_prompts,
            ):
                handled_any = True
                continue
            if self.click_enter_world_again_if_present(timeout_seconds=self._fast_timeout(1.2, 0.55)):
                handled_any = True
                continue
            if self.click_role_enter_battle_if_present(timeout_seconds=self._fast_timeout(1.2, 0.55)):
                handled_any = True
                continue
            if self.confirm_inactive_reselect_region_if_present(timeout_seconds=self._fast_timeout(1.2, 0.55)):
                handled_any = True
                continue
            if self.select_default_region_if_present(timeout_seconds=self._fast_timeout(1.2, 0.55)):
                handled_any = True
                continue
            if self.click_returning_player_enter_game_if_present():
                handled_any = True
                continue
            if self.click_season_bounty_start_if_present(timeout_seconds=self._fast_timeout(1.0, 0.35)):
                handled_any = True
                continue
            if self.skip_landscape_dialogs_if_present(max_taps=20, timeout_seconds=self._fast_timeout(0.5, 0.30)):
                handled_any = True
                continue
            if self.skip_portrait_dialogs_if_present(max_taps=30, timeout_seconds=self._fast_timeout(0.5, 0.30)):
                handled_any = True
                continue
            if self.click_any_visible_back_if_present(timeout_seconds=self._fast_timeout(0.35, 0.18)):
                handled_any = True
                continue

            self._record(
                {
                    "type": "state",
                    "state": "entry_preconditions_done",
                    "reason": "no_known_prompt_detected",
                    "round": index + 1,
                }
            )
            break
        return handled_any

    def click_title_enter_if_present(
        self,
        *,
        timeout_seconds: float = 0.8,
        click_login_after_prompt: bool = True,
    ) -> bool:
        self._record({"type": "state", "state": "click_title_enter_if_present"})
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        title_enter = self.wait_for_template(
            "进入游戏前置-标题页前往征战",
            "title_enter_button",
            timeout_seconds=timeout_seconds,
            threshold=0.78,
            region=(int(w * 0.20), int(h * 0.72), int(w * 0.60), int(h * 0.14)),
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "title_enter_button_precondition",
                "present": title_enter is not None,
                "x": title_enter.x if title_enter else None,
                "y": title_enter.y if title_enter else None,
                "width": title_enter.width if title_enter else None,
                "height": title_enter.height if title_enter else None,
                "score": round(title_enter.score, 4) if title_enter else 0.0,
            }
        )
        if not title_enter:
            return False

        self.tap("进入游戏前置-标题页前往征战", Point(*title_enter.center), wait_seconds=5.0)
        if click_login_after_prompt:
            if self.click_recent_login_account_if_present(timeout_seconds=1.0):
                self.click_account_login_modal_if_present(timeout_seconds=2.0)
            elif self.click_account_login_modal_if_present(timeout_seconds=2.0):
                pass
            self.click_login_secondary_confirm_if_present(timeout_seconds=1.0)
        else:
            login_surface = self.detect_account_login_surface(timeout_seconds=1.0)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "title_enter_opened_login_surface",
                    "present": login_surface,
                }
            )
        self.wait_for_template(
            "进入游戏前置-服务器排队弹窗",
            "queue_title",
            timeout_seconds=1.0,
            threshold=0.82,
            region=(int(w * 0.30), int(h * 0.35), int(w * 0.40), int(h * 0.12)),
        )
        self.screenshot("after_click_title_enter_precondition")
        return True

    def skip_landscape_dialogs_if_present(
        self,
        *,
        max_taps: int = 20,
        timeout_seconds: float = 0.7,
    ) -> bool:
        self._record(
            {
                "type": "state",
                "state": "skip_landscape_dialogs_if_present",
                "max_taps": max_taps,
            }
        )
        tapped = False
        for index in range(max(0, max_taps)):
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]
            if w <= h:
                self._record(
                    {
                        "type": "state",
                        "state": "landscape_dialogs_done",
                        "reason": "portrait_orientation",
                        "after_taps": index,
                    }
                )
                break

            region_enter = self.wait_for_template(
                "进入游戏前置-选择势力入驻按钮排除",
                "region_enter_label",
                timeout_seconds=0.15,
                threshold=0.72,
                region=(int(w * 0.68), int(h * 0.80), int(w * 0.30), int(h * 0.18)),
            )
            if region_enter:
                self._record(
                    {
                        "type": "state",
                        "state": "landscape_dialogs_done",
                        "reason": "region_enter_button_visible",
                        "after_taps": index,
                    }
                )
                break

            enter_world_again = self.wait_for_template(
                "进入游戏前置-再争乱世按钮排除",
                "enter_world_again_button",
                timeout_seconds=0.15,
                threshold=0.74,
                region=(int(w * 0.30), int(h * 0.76), int(w * 0.42), int(h * 0.18)),
            )
            if enter_world_again:
                self._record(
                    {
                        "type": "state",
                        "state": "landscape_dialogs_done",
                        "reason": "enter_world_again_button_visible",
                        "after_taps": index,
                        "score": round(enter_world_again.score, 4),
                    }
                )
                break

            continue_icon = self.wait_for_template(
                "进入游戏前置-横屏剧情继续箭头",
                "landscape_dialog_continue_icon",
                timeout_seconds=timeout_seconds,
                threshold=0.34,
                region=(int(w * 0.78), int(h * 0.60), int(w * 0.22), int(h * 0.38)),
            )
            if not continue_icon:
                self._record(
                    {
                        "type": "state",
                        "state": "landscape_dialogs_done",
                        "reason": "continue_icon_missing",
                        "after_taps": index,
                    }
                )
                break

            point = Point(*continue_icon.center)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "landscape_dialog_continue_icon",
                    "source": "template",
                    "x": continue_icon.x,
                    "y": continue_icon.y,
                    "width": continue_icon.width,
                    "height": continue_icon.height,
                    "score": round(continue_icon.score, 4),
                    "tap_x": point.x,
                    "tap_y": point.y,
                }
            )
            self.tap(f"进入游戏前置-跳过横屏剧情({index + 1})", point, wait_seconds=0.9)
            tapped = True

        if tapped:
            self.screenshot("after_skip_landscape_dialogs")
        return tapped

    def skip_portrait_dialogs_if_present(
        self,
        *,
        max_taps: int = 30,
        timeout_seconds: float = 0.7,
    ) -> bool:
        self._record(
            {
                "type": "state",
                "state": "skip_portrait_dialogs_if_present",
                "max_taps": max_taps,
            }
        )
        tapped = False
        unchanged_taps = 0
        for index in range(max(0, max_taps)):
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]
            if w >= h:
                self._record(
                    {
                        "type": "state",
                        "state": "portrait_dialogs_done",
                        "reason": "landscape_orientation",
                        "after_taps": index,
                    }
                )
                break

            if self.confirm_xiaomi_background_resources_if_present():
                tapped = True
                break

            title_marker_key, title_marker = self._detect_account_role_select_entry_marker(
                image,
                source="portrait_dialog_title_guard",
            )
            if title_marker_key in {"title_select_server", "title_enter_button"} and title_marker is not None:
                self._record(
                    {
                        "type": "state",
                        "state": "portrait_dialogs_done",
                        "reason": "title_screen_visible",
                        "after_taps": index,
                        "marker": title_marker_key,
                        "marker_score": round(title_marker.score, 4),
                    }
                )
                break

            full_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            full_edge_ratio = float((cv2.Canny(full_gray, 60, 140) > 0).mean())
            full_dark_ratio = float((full_gray < 70).mean())
            full_bright_ratio = float((full_gray > 130).mean())
            black_loading_screen = (
                full_dark_ratio >= 0.96
                and full_bright_ratio <= 0.01
                and full_edge_ratio <= 0.003
            )
            if black_loading_screen:
                self._record(
                    {
                        "type": "state",
                        "state": "portrait_dialogs_done",
                        "reason": "black_loading_screen",
                        "after_taps": index,
                        "full_dark_ratio": round(full_dark_ratio, 4),
                        "full_bright_ratio": round(full_bright_ratio, 4),
                        "full_edge_ratio": round(full_edge_ratio, 4),
                    }
                )
                self._sleep_with_watchdog(
                    self._fast_wait(1.0, 0.6),
                    source="portrait_dialog_black_loading_screen",
                )
                break

            region_guard = self._find_template_in_image(
                image,
                "region_enter_label",
                threshold=0.70,
                region=(int(w * 0.22), int(h * 0.84), int(w * 0.56), int(h * 0.15)),
            )
            if not region_guard:
                region_guard = self._find_template_in_image(
                    image,
                    "region_enter_selected_button",
                    threshold=0.70,
                    region=(int(w * 0.22), int(h * 0.84), int(w * 0.56), int(h * 0.15)),
                )
            if region_guard:
                self._record(
                    {
                        "type": "state",
                        "state": "portrait_dialogs_done",
                        "reason": "region_select_page_visible",
                        "after_taps": index,
                        "x": region_guard.x,
                        "y": region_guard.y,
                        "width": region_guard.width,
                        "height": region_guard.height,
                        "score": round(region_guard.score, 4),
                    }
                )
                break

            overlay = image[int(h * 0.50) : int(h * 0.70), int(w * 0.25) : int(w * 0.98)]
            overlay_gray = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
            overlay_mean = float(overlay_gray.mean())
            overlay_dark_ratio = float((overlay_gray < 70).mean())
            season_start_present, season_start_metrics, season_start_point = self.detect_season_bounty_start_in_image(image)
            if season_start_present:
                self._save_image_snapshot("before_click_season_bounty_start_from_portrait", image)
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "season_bounty_start_button",
                        "source": "portrait_dialog_guard",
                        **season_start_metrics,
                    }
                )
                self.tap(
                    "进入游戏前置-竖屏守卫点击赏金赛开始征战",
                    season_start_point,
                    wait_seconds=4.0,
                )
                tapped = True
                break
            recruit_visible = self._find_template_in_image(
                image,
                "main_recruit_button",
                threshold=0.62,
                region=(int(w * 0.76), int(h * 0.84), int(w * 0.24), int(h * 0.16)),
            )
            continue_icon = self._find_template_in_image(
                image,
                "dialog_continue_icon",
                threshold=0.45,
                region=(int(w * 0.76), int(h * 0.50), int(w * 0.24), int(h * 0.32)),
            )
            if not continue_icon:
                continue_icon = self.wait_for_template(
                    "进入游戏前置-竖屏剧情继续箭头",
                    "dialog_continue_icon",
                    timeout_seconds=min(timeout_seconds, 0.18),
                    threshold=0.45,
                    region=(int(w * 0.76), int(h * 0.50), int(w * 0.24), int(h * 0.32)),
                )
            back_key, back_button = self.find_any_visible_back_button_in_image(image)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "portrait_dialog_overlay",
                    "mean": round(overlay_mean, 1),
                    "dark_ratio": round(overlay_dark_ratio, 3),
                    "recruit_visible": recruit_visible is not None,
                    "continue_visible": continue_icon is not None,
                    "back_visible": back_button is not None,
                    "back_template": back_key,
                    "attempt": index + 1,
                }
            )
            if back_button:
                self._record(
                    {
                        "type": "state",
                        "state": "portrait_dialogs_done",
                        "reason": "visible_back_button_on_subpage",
                        "after_taps": index,
                    }
                )
                break
            if not continue_icon:
                self._record(
                    {
                        "type": "state",
                        "state": "portrait_dialogs_done",
                        "reason": "continue_icon_missing",
                        "after_taps": index,
                    }
                )
                break

            if recruit_visible and (overlay_mean > 92 or overlay_dark_ratio < 0.45):
                self._watchdog_reset()
                self._record(
                    {
                        "type": "state",
                        "state": "portrait_dialogs_done",
                        "reason": "main_screen_visible_with_false_continue_icon",
                        "after_taps": index,
                    }
                )
                break

            if recruit_visible and continue_icon.score < 0.50:
                self._watchdog_reset()
                self._record(
                    {
                        "type": "state",
                        "state": "portrait_dialogs_done",
                        "reason": "low_confidence_continue_icon_with_main_marker",
                        "after_taps": index,
                        "continue_score": round(continue_icon.score, 4),
                    }
                )
                break

            point = Point(*continue_icon.center)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "portrait_dialog_continue_icon",
                    "source": "template",
                    "x": continue_icon.x,
                    "y": continue_icon.y,
                    "width": continue_icon.width,
                    "height": continue_icon.height,
                    "score": round(continue_icon.score, 4),
                    "tap_x": point.x,
                    "tap_y": point.y,
                }
            )
            self.tap(f"进入游戏前置-跳过竖屏剧情({index + 1})", point, wait_seconds=0.9)
            tapped = True
            after_tap = self.bot.screenshot_image()
            change_score = self._roi_change_score(image, after_tap, 0, int(h * 0.42), w, h)
            unchanged_taps = unchanged_taps + 1 if change_score <= 0.15 else 0
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "portrait_dialog_after_tap_change",
                    "change_score": round(change_score, 4),
                    "unchanged_taps": unchanged_taps,
                }
            )
            if unchanged_taps >= 2:
                self._record(
                    {
                        "type": "state",
                        "state": "portrait_dialogs_done",
                        "reason": "repeated_tap_did_not_change_screen",
                        "after_taps": index + 1,
                    }
                )
                break

        if tapped:
            self.screenshot("after_skip_portrait_dialogs")
        return tapped

    def close_military_council_if_present(self, *, timeout_seconds: float = 1.0) -> bool:
        self._record({"type": "state", "state": "close_military_council_if_present"})
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        title = self._find_template_in_image(
            image,
            "military_council_title",
            threshold=0.72,
            region=(0, 0, int(w * 0.26), int(h * 0.12)),
        )
        if not title and timeout_seconds > 0.4:
            title = self.wait_for_template(
                "前置功能页-军议标题",
                "military_council_title",
                timeout_seconds=timeout_seconds,
                threshold=0.72,
                region=(0, 0, int(w * 0.26), int(h * 0.12)),
            )
        self._record(
            {
                "type": "vision_feature",
                "feature": "military_council_title",
                "present": title is not None,
                "x": title.x if title else None,
                "y": title.y if title else None,
                "width": title.width if title else None,
                "height": title.height if title else None,
                "score": round(title.score, 4) if title else 0.0,
            }
        )
        if not title:
            return False

        back = self.wait_for_template(
            "前置功能页-军议返回",
            "military_council_back_button",
            timeout_seconds=0.8,
            threshold=0.72,
            region=(0, int(h * 0.88), int(w * 0.34), int(h * 0.12)),
        )
        point = Point(*back.center) if back else Point(int(w * 0.16), int(h * 0.965))
        self._record(
            {
                "type": "vision_feature",
                "feature": "military_council_back_button",
                "present": back is not None,
                "source": "template" if back else "fallback",
                "x": back.x if back else point.x,
                "y": back.y if back else point.y,
                "width": back.width if back else None,
                "height": back.height if back else None,
                "score": round(back.score, 4) if back else 0.0,
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("前置功能页-返回军议", point, wait_seconds=2.0)
        self.screenshot("after_close_military_council")
        return True

    def close_exit_confirm_if_present(self, *, timeout_seconds: float = 1.0) -> bool:
        self._record({"type": "state", "state": "close_exit_confirm_if_present"})
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        title = self.detect_exit_confirm_in_image(image)
        if not title and timeout_seconds > 0.4:
            title = self.wait_for_template(
                "退出确认-标题",
                "exit_confirm_title",
                timeout_seconds=timeout_seconds,
                threshold=0.72,
                region=(int(w * 0.22), int(h * 0.35), int(w * 0.58), int(h * 0.18)),
            )
        self._record(
            {
                "type": "vision_feature",
                "feature": "exit_confirm_title",
                "present": title is not None,
                "x": title.x if title else None,
                "y": title.y if title else None,
                "width": title.width if title else None,
                "height": title.height if title else None,
                "score": round(title.score, 4) if title else 0.0,
            }
        )
        if not title:
            return False

        button = self._find_template_in_image(
            image,
            "exit_stay_button",
            threshold=0.72,
            region=(int(w * 0.44), int(h * 0.50), int(w * 0.52), int(h * 0.16)),
        )
        if not button:
            button = self.wait_for_template(
                "退出确认-再玩一会",
                "exit_stay_button",
                timeout_seconds=0.4,
                threshold=0.72,
                region=(int(w * 0.44), int(h * 0.50), int(w * 0.52), int(h * 0.16)),
            )
        point = Point(*button.center) if button else Point(int(w * 0.70), int(h * 0.565))
        self._record(
            {
                "type": "vision_feature",
                "feature": "exit_stay_button",
                "present": button is not None,
                "source": "template" if button else "fallback",
                "x": button.x if button else point.x,
                "y": button.y if button else point.y,
                "width": button.width if button else None,
                "height": button.height if button else None,
                "score": round(button.score, 4) if button else 0.0,
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("退出确认-点击再玩一会", point, wait_seconds=1.2)
        self.screenshot("after_close_exit_confirm")
        return True

    def select_last_entry_in_server_selector(self, *, confirm_and_enter: bool = True) -> Path:
        self._record({"type": "state", "state": "select_last_entry_in_server_selector"})
        self.open_server_selector()
        self.scroll_server_selector_to_bottom()
        rows = self.detect_server_selector_role_rows()
        row_fingerprint = None
        if rows:
            target = rows[-1]
            point = Point(int(target["tap_x"]), int(target["tap_y"]))
            row_fingerprint = self.fingerprint_server_selector_role_row(target)
            source = "avatar_color_rows"
        else:
            center_x, _, bottom = self.detect_server_selector_bounds()
            point = Point(center_x, bottom - 18)
            source = "selector_bottom_fallback"
        self._record(
            {
                "type": "vision_feature",
                "feature": "server_selector_last_entry_tap",
                "source": source,
                "x": point.x,
                "y": point.y,
                "row_fingerprint": row_fingerprint,
            }
        )
        self.tap(
            "选服列表-选择最后一个角色",
            point,
            wait_seconds=0.8,
        )
        selected_path = self.screenshot("after_select_last_server_entry")
        if not confirm_and_enter:
            return selected_path

        self.tap_server_selector_confirm(
            "选服列表-确定最后一个角色",
            wait_seconds=1.5,
        )
        self.screenshot("after_confirm_last_server_entry")
        self.enter_selected_server(wait_seconds=8.0)
        self.handle_entry_preconditions(max_rounds=8)
        self.close_signin_reward_if_present(timeout_seconds=2.0)
        return self.screenshot("after_enter_last_server_entry")

    def select_last_role_in_server_selector(self) -> Path:
        return self.select_last_entry_in_server_selector(confirm_and_enter=False)

    def confirm_selected_server_entry_and_enter(self) -> Path:
        self._record({"type": "state", "state": "confirm_selected_server_entry_and_enter"})
        self.tap_server_selector_confirm(
            "选服列表-确定当前选中角色",
            wait_seconds=1.5,
        )
        self.screenshot("after_confirm_selected_server_entry")
        self.enter_selected_server(wait_seconds=8.0)
        self.handle_entry_preconditions(max_rounds=8)
        self.close_signin_reward_if_present(timeout_seconds=2.0)
        return self.screenshot("after_enter_selected_server_entry")

    def close_signin_reward_if_present(self, *, timeout_seconds: float = 1.2) -> bool:
        self._record({"type": "state", "state": "check_signin_reward_prompt"})
        self._watchdog_reset()
        image = self.bot.screenshot_image()
        self._save_image_snapshot("before_check_signin_reward_prompt", image)
        self._watchdog_maybe_check(source="screenshot:before_check_signin_reward_prompt", image=image)

        h, w = image.shape[:2]
        selector = self.detect_server_selector_title_in_image(image, threshold=0.72)
        if selector:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "signin_reward_prompt",
                    "present": False,
                    "source": "server_selector_reject",
                    "selector_x": selector.x,
                    "selector_y": selector.y,
                    "selector_width": selector.width,
                    "selector_height": selector.height,
                    "selector_score": round(selector.score, 4),
                }
            )
            return False

        inactive_present, inactive_metrics, _ = self.detect_inactive_reselect_prompt_in_image(
            image,
            threshold=0.62,
        )
        if inactive_present:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "signin_reward_prompt",
                    "present": False,
                    "source": "inactive_reselect_reject",
                    "inactive_reselect": inactive_metrics,
                }
            )
            return False

        known_retreat_region = (int(w * 0.20), int(h * 0.42), int(w * 0.45), int(h * 0.18))
        known_retreat = self._find_template_in_image(
            image,
            "main_known_retreat_button",
            threshold=0.74,
            region=known_retreat_region,
        )
        if known_retreat:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "signin_reward_prompt",
                    "present": False,
                    "source": "known_retreat_prompt_reject",
                    "known_retreat_x": known_retreat.x,
                    "known_retreat_y": known_retreat.y,
                    "known_retreat_width": known_retreat.width,
                    "known_retreat_height": known_retreat.height,
                    "known_retreat_score": round(known_retreat.score, 4),
                }
            )
            return False

        def signin_overlay_dark_metrics(current: np.ndarray) -> tuple[float, float, float]:
            current_h, current_w = current.shape[:2]
            panel_crop = self._crop(
                current,
                (int(current_w * 0.08), int(current_h * 0.38), int(current_w * 0.84), int(current_h * 0.28)),
            )
            center_crop = self._crop(
                current,
                (int(current_w * 0.08), int(current_h * 0.25), int(current_w * 0.84), int(current_h * 0.45)),
            )
            panel_gray = cv2.cvtColor(panel_crop, cv2.COLOR_BGR2GRAY)
            center_gray = cv2.cvtColor(center_crop, cv2.COLOR_BGR2GRAY)
            full_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
            return (
                float((panel_gray < 90).mean()),
                float((center_gray < 90).mean()),
                float((full_gray < 90).mean()),
            )

        panel_dark_ratio, center_dark_ratio, full_dark_ratio = signin_overlay_dark_metrics(image)
        if panel_dark_ratio < 0.55 and center_dark_ratio < 0.55 and full_dark_ratio < 0.55:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "signin_reward_prompt",
                    "present": False,
                    "source": "dark_overlay_fast_reject",
                    "panel_dark_ratio": round(panel_dark_ratio, 3),
                    "center_dark_ratio": round(center_dark_ratio, 3),
                    "full_dark_ratio": round(full_dark_ratio, 3),
                }
            )
            return False

        title = None
        title_key = None
        button = None
        button_key = None
        point: Point | None = None
        source = "template"
        score = 0.0
        for candidate_key in ("signin_reward_title", "signin_reward_title_small"):
            title = self.wait_for_template(
                "今日签到奖励-标题",
                candidate_key,
                timeout_seconds=timeout_seconds,
                threshold=0.66,
                region=None,
            )
            if title:
                title_key = candidate_key
                break

        if not title:
            confirm_region = (int(w * 0.34), int(h * 0.54), int(w * 0.32), int(h * 0.16))
            for candidate_key in ("signin_reward_confirm_button", "signin_reward_confirm_button_small"):
                button = self.wait_for_template(
                    "今日签到奖励-确认-无标题兜底",
                    candidate_key,
                    timeout_seconds=min(0.8, max(0.3, timeout_seconds)),
                    threshold=0.62,
                    region=confirm_region,
                )
                if button:
                    button_key = candidate_key
                    break

            if button:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "signin_reward_button_without_title_overlay_check",
                        "panel_dark_ratio": round(panel_dark_ratio, 3),
                        "center_dark_ratio": round(center_dark_ratio, 3),
                        "full_dark_ratio": round(full_dark_ratio, 3),
                    }
                )
                if panel_dark_ratio >= 0.75 and center_dark_ratio >= 0.70 and full_dark_ratio >= 0.70:
                    point = Point(*button.center)
                    source = "button_template_without_title"
                    score = round(button.score, 4)
            else:
                confirm_crop = self._crop(image, confirm_region)
                confirm_gray = cv2.cvtColor(confirm_crop, cv2.COLOR_BGR2GRAY)
                bright_ratio = float((confirm_gray > 145).mean())
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "signin_reward_visual_fallback",
                        "bright_ratio": round(bright_ratio, 3),
                        "panel_dark_ratio": round(panel_dark_ratio, 3),
                        "center_dark_ratio": round(center_dark_ratio, 3),
                        "full_dark_ratio": round(full_dark_ratio, 3),
                        "region_x": confirm_region[0],
                        "region_y": confirm_region[1],
                        "region_width": confirm_region[2],
                        "region_height": confirm_region[3],
                    }
                )
                if (
                    bright_ratio >= 0.10
                    and panel_dark_ratio >= 0.75
                    and center_dark_ratio >= 0.70
                    and full_dark_ratio >= 0.70
                ):
                    point = Point(int(w * 0.50), int(h * 0.62))
                    source = "visual_fallback_without_title"
                    score = round(bright_ratio, 4)

            if point is None:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "signin_reward_prompt",
                        "present": False,
                    }
                )
                return False

        self._record(
            {
                "type": "vision_feature",
                "feature": "signin_reward_prompt",
                "present": True,
                "title_template": title_key,
                "title_x": title.x if title else None,
                "title_y": title.y if title else None,
                "title_width": title.width if title else None,
                "title_height": title.height if title else None,
                "title_score": round(title.score, 4) if title else 0.0,
            }
        )

        if title and point is None:
            for candidate_key in ("signin_reward_confirm_button", "signin_reward_confirm_button_small"):
                button = self.wait_for_template(
                    "今日签到奖励-确认",
                    candidate_key,
                    timeout_seconds=timeout_seconds,
                    threshold=0.66,
                    region=None,
                )
                if button:
                    button_key = candidate_key
                    break

        if point is None:
            if button:
                point = Point(*button.center)
                source = "template"
                score = round(button.score, 4)
            else:
                point = Point(int(w * 0.5), int(min(h - 80, title.y + title.height + h * 0.16)))
                source = "fallback"
                score = 0.0

        def signin_prompt_still_visible() -> bool:
            for candidate_key in ("signin_reward_title", "signin_reward_title_small"):
                if self.wait_for_template(
                    "今日签到奖励-复查标题",
                    candidate_key,
                    timeout_seconds=0.35,
                    threshold=0.66,
                    region=None,
                ):
                    return True

            check_image = self.bot.screenshot_image()
            check_h, check_w = check_image.shape[:2]
            check_region = (int(check_w * 0.34), int(check_h * 0.54), int(check_w * 0.32), int(check_h * 0.16))
            check_crop = self._crop(check_image, check_region)
            check_gray = cv2.cvtColor(check_crop, cv2.COLOR_BGR2GRAY)
            check_panel = self._crop(
                check_image,
                (int(check_w * 0.08), int(check_h * 0.38), int(check_w * 0.84), int(check_h * 0.28)),
            )
            check_panel_gray = cv2.cvtColor(check_panel, cv2.COLOR_BGR2GRAY)
            check_center = self._crop(
                check_image,
                (int(check_w * 0.08), int(check_h * 0.25), int(check_w * 0.84), int(check_h * 0.45)),
            )
            check_center_gray = cv2.cvtColor(check_center, cv2.COLOR_BGR2GRAY)
            check_full_gray = cv2.cvtColor(check_image, cv2.COLOR_BGR2GRAY)
            check_bright_ratio = float((check_gray > 145).mean())
            check_dark_ratio = float((check_panel_gray < 90).mean())
            check_center_dark_ratio = float((check_center_gray < 90).mean())
            check_full_dark_ratio = float((check_full_gray < 90).mean())
            return (
                check_bright_ratio >= 0.10
                and check_dark_ratio >= 0.75
                and check_center_dark_ratio >= 0.70
                and check_full_dark_ratio >= 0.70
            )

        for attempt in range(1, 4):
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "signin_reward_confirm_button",
                    "attempt": attempt,
                    "source": source,
                    "template": button_key,
                    "x": point.x,
                    "y": point.y,
                    "score": score,
                }
            )
            self.tap(f"今日签到奖励-确认({attempt})", point, wait_seconds=1.0)
            self.screenshot(f"after_signin_reward_confirm_{attempt}")

            still_present = signin_prompt_still_visible()

            self._record(
                {
                    "type": "vision_feature",
                    "feature": "signin_reward_retry_check",
                    "attempt": attempt,
                    "still_present": still_present,
                }
            )
            if not still_present:
                break
        if self.detect_like_main_screen():
            self._record(
                {
                    "type": "state",
                    "state": "signin_reward_skip_orange_scan",
                    "reason": "main_screen_detected_after_confirm",
                }
            )
            return True
        self.skip_orange_card_effect_if_present(timeout_seconds=8.0)
        self.close_orange_card_detail_if_present(timeout_seconds=3.0)
        return True

    def complete_signin_reward_prompt(self) -> Path:
        closed = self.close_signin_reward_if_present(timeout_seconds=1.5)
        self._record(
            {
                "type": "state",
                "state": "signin_reward_prompt_done",
                "closed": closed,
            }
        )
        return self.screenshot("after_signin_reward_prompt")

    def detect_orange_card_effect_page(self, image: np.ndarray) -> tuple[bool, dict[str, float]]:
        h, w = image.shape[:2]
        title_enter = self._find_template_in_image(
            image,
            "title_enter_button",
            threshold=0.68,
            region=(int(w * 0.20), int(h * 0.72), int(w * 0.60), int(h * 0.14)),
        )
        exit_confirm = self.detect_exit_confirm_in_image(image, threshold=0.68)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        lower_gray = gray[int(h * 0.62) : int(h * 0.94), :]
        screen_dark_ratio = float((gray < 70).mean())
        lower_dark_ratio = float((lower_gray < 70).mean())
        screen_mean = float(gray.mean())
        lower_mean = float(lower_gray.mean())
        bottom_dialog = gray[int(h * 0.70) : int(h * 0.88), :]
        bottom_dialog_dark_ratio = float((bottom_dialog < 70).mean()) if bottom_dialog.size else 0.0
        portrait_region = image[int(h * 0.18) : int(h * 0.72), int(w * 0.12) : int(w * 0.88)]
        portrait_gray = cv2.cvtColor(portrait_region, cv2.COLOR_BGR2GRAY)
        portrait_edge_ratio = (
            float((cv2.Canny(portrait_gray, 60, 120) > 0).mean())
            if portrait_gray.size
            else 0.0
        )
        present = (
            w < h
            and title_enter is None
            and exit_confirm is None
            and screen_dark_ratio >= 0.74
            and lower_dark_ratio >= 0.88
            and bottom_dialog_dark_ratio >= 0.86
            and portrait_edge_ratio >= 0.035
        )
        metrics = {
            "screen_mean": screen_mean,
            "screen_dark_ratio": screen_dark_ratio,
            "lower_mean": lower_mean,
            "lower_dark_ratio": lower_dark_ratio,
            "bottom_dialog_dark_ratio": bottom_dialog_dark_ratio,
            "portrait_edge_ratio": portrait_edge_ratio,
            "title_enter_score": float(title_enter.score) if title_enter else 0.0,
            "exit_confirm_score": float(exit_confirm.score) if exit_confirm else 0.0,
        }
        return present, metrics

    def find_orange_card_down_arrow(
        self,
        image: np.ndarray | None = None,
    ) -> tuple[Point, str, float] | None:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        is_orange_page, metrics = self.detect_orange_card_effect_page(image)
        self._record(
            {
                "type": "vision_feature",
                "feature": "orange_card_context",
                "present": is_orange_page,
                "screen_mean": round(metrics["screen_mean"], 1),
                "screen_dark_ratio": round(metrics["screen_dark_ratio"], 3),
                "lower_mean": round(metrics["lower_mean"], 1),
                "lower_dark_ratio": round(metrics["lower_dark_ratio"], 3),
                "bottom_dialog_dark_ratio": round(metrics["bottom_dialog_dark_ratio"], 3),
                "portrait_edge_ratio": round(metrics["portrait_edge_ratio"], 4),
            }
        )
        recruit = self._find_template_in_image(
            image,
            "main_recruit_button",
            threshold=0.62,
            region=(int(w * 0.76), int(h * 0.84), int(w * 0.24), int(h * 0.16)),
        )
        if recruit:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "orange_card_context",
                    "rejected_reason": "main_recruit_button_visible",
                    "recruit_score": round(recruit.score, 4),
                }
            )
            return None

        if not is_orange_page:
            return None

        region = (
            int(w * 0.78),
            int(h * 0.74),
            int(w * 0.21),
            int(h * 0.18),
        )

        template_candidates = (
            ("gacha_orange_card_down_arrow", 0.50),
            ("orange_card_down_arrow", 0.50),
        )
        for template_key, threshold in template_candidates:
            match = self._find_template_in_image(
                image,
                template_key,
                threshold=threshold,
                region=region,
            )
            if match:
                return Point(*match.center), f"template:{template_key}", float(match.score)

        x1, y1, rw, rh = region
        crop = image[y1 : y1 + rh, x1 : x1 + rw]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        gold_mask = cv2.inRange(hsv, np.array([14, 35, 80]), np.array([46, 255, 255]))
        bright_mask = (((hsv[:, :, 2] > 150) & (hsv[:, :, 1] < 130)) | (hsv[:, :, 2] > 190)).astype("uint8") * 255
        mask = cv2.bitwise_or(gold_mask, bright_mask)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates: list[tuple[float, int, int, int, int]] = []
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            area = float(cv2.contourArea(contour))
            if area < 25:
                continue
            if not (10 <= width <= 62 and 10 <= height <= 62):
                continue
            aspect = width / max(1, height)
            if not (0.55 <= aspect <= 1.85):
                continue
            absolute_x = x1 + x
            absolute_y = y1 + y
            position_bonus = (absolute_x / max(1, w)) + (absolute_y / max(1, h))
            candidates.append((area + position_bonus * 80, absolute_x, absolute_y, width, height))

        if candidates:
            _, x, y, width, height = max(candidates, key=lambda item: item[0])
            return Point(int(x + width / 2), int(y + height / 2)), "gold_or_bright_contour", float(width * height)

        return Point(int(w * 0.918), int(h * 0.826)), "orange_page_coordinate_fallback", 1.0

    def find_click_other_area_return_hint(
        self,
        image: np.ndarray,
    ) -> tuple[Point, str, Match] | None:
        h, w = image.shape[:2]
        region = (
            0,
            int(h * 0.82),
            w,
            int(h * 0.18),
        )

        for candidate_key in (
            "click_other_area_return_hint_game",
            "click_other_area_return_hint",
            "click_other_area_return_hint_game_x2",
            "click_other_area_return_hint_x2",
        ):
            found = self._find_template_in_image(
                image,
                candidate_key,
                threshold=0.50,
                region=region,
            )
            if found:
                return Point(int(w * 0.5), int(h * 0.96)), candidate_key, found
        return None

    def close_orange_card_detail_if_present(self, *, timeout_seconds: float = 3.0) -> bool:
        self._record({"type": "state", "state": "close_orange_card_detail_if_present"})
        self.screenshot("before_close_orange_card_detail")
        end_at = time() + timeout_seconds
        attempt = 0
        while time() < end_at:
            attempt += 1
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]

            hint = self.find_click_other_area_return_hint(image)
            if hint:
                point, found_key, found = hint
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "orange_card_detail_return_hint",
                        "attempt": attempt,
                        "source": "template",
                        "template": found_key,
                        "match_x": found.x,
                        "match_y": found.y,
                        "match_width": found.width,
                        "match_height": found.height,
                        "x": point.x,
                        "y": point.y,
                        "score": round(found.score, 4),
                    }
                )
                self.tap(f"橙卡详情-点击其他区域返回({attempt})-第一次", point, wait_seconds=1.2)
                self.tap(f"橙卡详情-点击其他区域返回({attempt})-第二次", point, wait_seconds=0.6)
                self.screenshot("after_close_orange_card_detail")
                return True

            is_orange_page, metrics = self.detect_orange_card_effect_page(image)
            recruit = self._find_template_in_image(
                image,
                "main_recruit_button",
                threshold=0.62,
                region=(int(w * 0.76), int(h * 0.84), int(w * 0.24), int(h * 0.16)),
            )
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "orange_card_detail_context",
                    "attempt": attempt,
                    "present": is_orange_page and recruit is None,
                    "screen_dark_ratio": round(metrics["screen_dark_ratio"], 3),
                    "lower_dark_ratio": round(metrics["lower_dark_ratio"], 3),
                    "bottom_dialog_dark_ratio": round(metrics["bottom_dialog_dark_ratio"], 3),
                    "portrait_edge_ratio": round(metrics["portrait_edge_ratio"], 4),
                    "recruit_score": round(recruit.score, 4) if recruit else 0.0,
                }
            )
            if is_orange_page and recruit is None:
                point = Point(int(w * 0.5), int(h * 0.96))
                self.tap(f"橙卡详情-坐标兜底返回({attempt})-第一次", point, wait_seconds=1.2)
                self.tap(f"橙卡详情-坐标兜底返回({attempt})-第二次", point, wait_seconds=0.6)
                self.screenshot("after_close_orange_card_detail_fallback")
                return True

            self._sleep_with_watchdog(0.35, source="orange_card_detail_scan")

        self.screenshot("orange_card_detail_not_seen")
        return False

    def skip_orange_card_effect_if_present(self, *, timeout_seconds: float = 8.0) -> bool:
        self._record({"type": "state", "state": "skip_orange_card_effect_if_present"})
        self.screenshot("before_skip_orange_card_effect")
        end_at = time() + timeout_seconds
        attempt = 0
        while time() < end_at:
            attempt += 1
            try:
                image = self.bot.screenshot_image()
            except Exception as exc:  # noqa: BLE001 - ADB can transiently stall during card animations.
                self._record(
                    {
                        "type": "state",
                        "state": "orange_card_screenshot_retry",
                        "attempt": attempt,
                        "error": str(exc),
                    }
                )
                self._sleep_with_watchdog(0.5, source="orange_card_screenshot_retry")
                continue

            hint = self.find_click_other_area_return_hint(image)
            if hint:
                point, found_key, found = hint
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "orange_card_detail_return_hint",
                        "attempt": attempt,
                        "source": "skip_orange_card_effect",
                        "template": found_key,
                        "match_x": found.x,
                        "match_y": found.y,
                        "match_width": found.width,
                        "match_height": found.height,
                        "x": point.x,
                        "y": point.y,
                        "score": round(found.score, 4),
                    }
                )
                self.tap(f"橙卡详情-点击其他区域返回({attempt})-第一次", point, wait_seconds=1.2)
                self.tap(f"橙卡详情-点击其他区域返回({attempt})-第二次", point, wait_seconds=0.6)
                self.screenshot("after_skip_orange_card_detail")
                return True

            found = self.find_orange_card_down_arrow(image)
            if found:
                point, source, score = found
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "orange_card_down_arrow",
                        "attempt": attempt,
                        "source": source,
                        "x": point.x,
                        "y": point.y,
                        "score": round(score, 4),
                }
                )
                self.tap(f"橙卡特效-点击向下箭头({attempt})", point, wait_seconds=1.0)
                self.screenshot("after_skip_orange_card_effect")
                self.click_other_area_return_hint_if_present(timeout_seconds=5.0)
                return True

            self._record(
                {
                    "type": "vision_feature",
                    "feature": "orange_card_down_arrow",
                    "attempt": attempt,
                    "present": False,
                }
            )
            self._sleep_with_watchdog(0.35, source="orange_card_effect_scan")

        self.screenshot("orange_card_effect_not_seen")
        return False

    def find_gacha_showcase_continue_point(
        self,
        image: np.ndarray | None = None,
        *,
        record: bool = True,
    ) -> tuple[Point, str, float] | None:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            if record:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "gacha_showcase_continue",
                        "present": False,
                        "reason": "landscape_screen",
                    }
                )
            return None

        recruit = self._find_template_in_image(
            image,
            "main_recruit_button",
            threshold=0.62,
            region=(int(w * 0.76), int(h * 0.84), int(w * 0.24), int(h * 0.16)),
        )
        if recruit:
            if record:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "gacha_showcase_continue",
                        "present": False,
                        "reason": "main_recruit_button_visible",
                        "recruit_score": round(recruit.score, 4),
                    }
                )
            return None

        result_back = self._find_template_in_image(
            image,
            "gacha_result_back_button",
            threshold=0.70,
            region=(0, int(h * 0.90), int(w * 0.30), int(h * 0.10)),
        )
        if result_back:
            if record:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "gacha_showcase_continue",
                        "present": False,
                        "reason": "result_back_button_visible",
                        "back_score": round(result_back.score, 4),
                    }
                )
            return None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        dialog = gray[int(h * 0.72) : int(h * 0.90), :]
        portrait = gray[int(h * 0.18) : int(h * 0.73), int(w * 0.15) : int(w * 0.85)]
        bottom_left = gray[int(h * 0.90) : h, 0 : int(w * 0.30)]

        screen_dark_ratio = float((gray < 70).mean())
        dialog_dark_ratio = float((dialog < 70).mean()) if dialog.size else 0.0
        portrait_edge_ratio = (
            float((cv2.Canny(portrait, 60, 140) > 0).mean()) if portrait.size else 0.0
        )
        bottom_left_dark_ratio = float((bottom_left < 70).mean()) if bottom_left.size else 0.0

        present = (
            screen_dark_ratio >= 0.55
            and dialog_dark_ratio >= 0.88
            and portrait_edge_ratio >= 0.075
            and bottom_left_dark_ratio >= 0.94
        )
        if not present:
            if record:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "gacha_showcase_continue",
                        "present": False,
                        "screen_dark_ratio": round(screen_dark_ratio, 3),
                        "dialog_dark_ratio": round(dialog_dark_ratio, 3),
                        "portrait_edge_ratio": round(portrait_edge_ratio, 4),
                        "bottom_left_dark_ratio": round(bottom_left_dark_ratio, 3),
                    }
                )
            return None

        region = (int(w * 0.84), int(h * 0.76), int(w * 0.15), int(h * 0.12))
        x1, y1, rw, rh = self._clip_region(image, region)
        crop = image[y1 : y1 + rh, x1 : x1 + rw]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        gold_mask = cv2.inRange(hsv, np.array([14, 25, 70]), np.array([48, 255, 255]))
        bright_mask = (((hsv[:, :, 2] > 145) & (hsv[:, :, 1] < 150)) | (hsv[:, :, 2] > 205)).astype(
            "uint8"
        ) * 255
        mask = cv2.bitwise_or(gold_mask, bright_mask)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates: list[tuple[float, int, int, int, int]] = []
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            area = float(cv2.contourArea(contour))
            if area < 8:
                continue
            if not (6 <= width <= 54 and 6 <= height <= 54):
                continue
            aspect = width / max(1, height)
            if not (0.45 <= aspect <= 2.30):
                continue
            absolute_x = x1 + x
            absolute_y = y1 + y
            position_bonus = (absolute_x / max(1, w)) + (absolute_y / max(1, h))
            candidates.append((area + position_bonus * 20, absolute_x, absolute_y, width, height))

        if candidates:
            score, x, y, width, height = max(candidates, key=lambda item: item[0])
            point = Point(int(x + width / 2), int(y + height / 2))
            source = "gold_or_bright_contour"
        else:
            point = Point(int(w * 0.918), int(h * 0.826))
            source = "showcase_coordinate_fallback"
            score = 1.0

        if record:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "gacha_showcase_continue",
                    "present": True,
                    "source": source,
                    "screen_dark_ratio": round(screen_dark_ratio, 3),
                    "dialog_dark_ratio": round(dialog_dark_ratio, 3),
                    "portrait_edge_ratio": round(portrait_edge_ratio, 4),
                    "bottom_left_dark_ratio": round(bottom_left_dark_ratio, 3),
                    "candidate_count": len(candidates),
                    "x": point.x,
                    "y": point.y,
                    "score": round(float(score), 4),
                }
            )
        return point, source, float(score)

    def advance_gacha_showcase_if_present(self, *, timeout_seconds: float = 4.0) -> bool:
        self._record({"type": "state", "state": "advance_gacha_showcase_if_present"})
        end_at = time() + max(0.1, timeout_seconds)
        attempt = 0
        while time() < end_at:
            attempt += 1
            image = self.bot.screenshot_image()
            found = self.find_gacha_showcase_continue_point(image)
            if found:
                point, source, score = found
                self._save_image_snapshot("before_click_gacha_showcase_continue", image)
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "gacha_showcase_continue_button",
                        "attempt": attempt,
                        "source": source,
                        "x": point.x,
                        "y": point.y,
                        "score": round(score, 4),
                    }
                )
                self._watchdog_reset()
                self.tap(f"抽卡流程-点击武将展示继续({attempt})", point, wait_seconds=1.2)
                self.screenshot("after_click_gacha_showcase_continue")
                return True

            self._sleep_with_watchdog(0.3, source="gacha_showcase_continue_scan")

        self.screenshot("gacha_showcase_continue_not_seen")
        return False

    def click_other_area_return_hint_if_present(self, *, timeout_seconds: float = 4.0) -> bool:
        self._record({"type": "state", "state": "click_other_area_return_hint_if_present"})
        self.screenshot("before_click_other_area_return_hint")
        end_at = time() + timeout_seconds
        attempt = 0
        while time() < end_at:
            attempt += 1
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]
            region = (
                0,
                int(h * 0.82),
                w,
                int(h * 0.18),
            )

            found = None
            found_key = None
            for candidate_key in (
                "click_other_area_return_hint_game",
                "click_other_area_return_hint",
                "click_other_area_return_hint_game_x2",
                "click_other_area_return_hint_x2",
            ):
                found = self.wait_for_template(
                    "点击其他区域返回提示",
                    candidate_key,
                    timeout_seconds=0.45,
                    threshold=0.50,
                    region=region,
                )
                if found:
                    found_key = candidate_key
                    break

            if found:
                point = Point(int(w * 0.5), int(h * 0.96))
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "click_other_area_return_hint",
                        "attempt": attempt,
                        "source": "template",
                        "template": found_key,
                        "match_x": found.x,
                        "match_y": found.y,
                        "match_width": found.width,
                        "match_height": found.height,
                        "x": point.x,
                        "y": point.y,
                        "score": round(found.score, 4),
                    }
                )
                self.tap(f"点击其他区域返回({attempt})-第一次", point, wait_seconds=2.0)
                self.tap(f"点击其他区域返回({attempt})-第二次", point, wait_seconds=1.0)
                self.screenshot("after_click_other_area_return_hint")
                return True

            bottom = image[int(h * 0.92) : int(h * 0.99), int(w * 0.25) : int(w * 0.75)]
            hsv = cv2.cvtColor(bottom, cv2.COLOR_BGR2HSV)
            light_ratio = float((((hsv[:, :, 2] > 135) & (hsv[:, :, 1] < 95))).mean())
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "click_other_area_return_hint",
                    "attempt": attempt,
                    "present": False,
                    "source": "template_only",
                    "light_ratio": round(light_ratio, 5),
                }
            )
            self._sleep_with_watchdog(0.35, source="click_other_area_return_hint_scan")

        self.screenshot("click_other_area_return_hint_not_seen")
        return False

    def complete_click_other_area_return_hint(self) -> Path:
        clicked = self.click_other_area_return_hint_if_present(timeout_seconds=5.0)
        self._record(
            {
                "type": "state",
                "state": "click_other_area_return_hint_done",
                "clicked": clicked,
            }
        )
        return self.screenshot("after_click_other_area_return_hint_node")

    def back_to_main_from_alliance(self) -> Path:
        self._record({"type": "state", "state": "back_to_main_from_alliance"})
        self.screenshot("before_alliance_back_to_main")
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (0, int(h * 0.88), int(w * 0.34), int(h * 0.12))

        found = None
        found_key = None
        for candidate_key in ("alliance_back_button", "alliance_back_button_x2"):
            found = self.wait_for_template(
                "同盟页-返回按钮",
                candidate_key,
                timeout_seconds=0.8,
                threshold=0.62,
                region=region,
            )
            if found:
                found_key = candidate_key
                break

        if found:
            point = Point(*found.center)
            source = "template"
            score = round(found.score, 4)
        else:
            point = Point(int(w * 0.14), int(h * 0.965))
            source = "fallback"
            score = 0.0

        self._record(
            {
                "type": "vision_feature",
                "feature": "alliance_back_button",
                "source": source,
                "template": found_key,
                "x": point.x,
                "y": point.y,
                "score": score,
            }
        )
        self.tap("同盟页-返回主界面", point, wait_seconds=1.5)
        return self.screenshot("after_alliance_back_to_main")

    def detect_like_main_screen(self) -> bool:
        self._record({"type": "state", "state": "detect_like_main_screen"})
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (int(w * 0.78), int(h * 0.86), int(w * 0.22), int(h * 0.14))

        full_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        full_dark_ratio = float((full_gray < 70).mean())
        overlay_mean = 255.0
        overlay_dark_ratio = 0.0
        continue_icon = None
        if w < h:
            overlay = image[int(h * 0.50) : int(h * 0.70), int(w * 0.25) : int(w * 0.98)]
            overlay_gray = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
            overlay_mean = float(overlay_gray.mean())
            overlay_dark_ratio = float((overlay_gray < 70).mean())
            continue_icon = self._find_template_in_image(
                image,
                "dialog_continue_icon",
                threshold=0.45,
                region=(int(w * 0.76), int(h * 0.50), int(w * 0.24), int(h * 0.32)),
            )
        overlay_blocks_main = (
            full_dark_ratio >= 0.72
            or (
                overlay_mean <= 92
                and overlay_dark_ratio >= 0.45
                and continue_icon is not None
            )
        )
        if overlay_blocks_main:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "like_main_screen_rejected_dialog_overlay",
                    "full_dark_ratio": round(full_dark_ratio, 3),
                    "overlay_mean": round(overlay_mean, 1),
                    "overlay_dark_ratio": round(overlay_dark_ratio, 3),
                    "continue_x": continue_icon.x if continue_icon else None,
                    "continue_y": continue_icon.y if continue_icon else None,
                    "continue_score": round(continue_icon.score, 4) if continue_icon else 0.0,
                    "reason": (
                        "full_screen_too_dark"
                        if full_dark_ratio >= 0.72
                        else "dialog_overlay_present"
                    ),
                }
            )
            return False

        recruit = self._find_template_in_image(
            image,
            "main_recruit_button",
            threshold=0.68,
            region=region,
        )
        if not recruit:
            recruit = self.wait_for_template(
                "点赞流程-主界面招募参照",
                "main_recruit_button",
                timeout_seconds=self.main_template_timeout_seconds,
                threshold=0.68,
                region=region,
            )
        if recruit:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "like_main_screen_recruit_button",
                    "present": True,
                    "source": "template",
                    "timeout_seconds": self.main_template_timeout_seconds,
                    "x": recruit.x,
                    "y": recruit.y,
                    "width": recruit.width,
                    "height": recruit.height,
                    "score": round(recruit.score, 4),
                }
            )
            self._watchdog_reset()
            return True

        x, y, width, height = region
        crop = image[y : y + height, x : x + width]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, np.array([35, 55, 55]), np.array([95, 255, 255]))
        green_ratio = float(cv2.countNonZero(green_mask)) / float(max(1, width * height))

        bottom_bar = image[int(h * 0.94) : int(h * 0.995), int(w * 0.18) : int(w * 0.80)]
        left_menu = image[int(h * 0.72) : int(h * 0.88), 0 : int(w * 0.24)]
        bottom_gray = cv2.cvtColor(bottom_bar, cv2.COLOR_BGR2GRAY)
        left_gray = cv2.cvtColor(left_menu, cv2.COLOR_BGR2GRAY)
        bottom_dark_ratio = float((bottom_gray < 70).mean()) if bottom_gray.size else 0.0
        bottom_bright_ratio = float((bottom_gray > 180).mean()) if bottom_gray.size else 0.0
        bottom_edge_ratio = (
            float((cv2.Canny(bottom_gray, 60, 120) > 0).mean()) if bottom_gray.size else 0.0
        )
        left_dark_ratio = float((left_gray < 70).mean()) if left_gray.size else 0.0
        left_edge_ratio = (
            float((cv2.Canny(left_gray, 60, 120) > 0).mean()) if left_gray.size else 0.0
        )
        main_ui_present = (
            bottom_dark_ratio >= 0.16
            and bottom_bright_ratio >= 0.03
            and bottom_edge_ratio >= 0.10
        ) or (left_dark_ratio >= 0.14 and left_edge_ratio >= 0.12)

        if green_ratio > 0.08 and main_ui_present:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "like_main_screen_recruit_button",
                    "present": True,
                    "source": "green_color_fallback",
                    "region_x": x,
                    "region_y": y,
                    "region_width": width,
                    "region_height": height,
                    "green_ratio": round(green_ratio, 4),
                    "bottom_dark_ratio": round(bottom_dark_ratio, 4),
                    "bottom_bright_ratio": round(bottom_bright_ratio, 4),
                    "bottom_edge_ratio": round(bottom_edge_ratio, 4),
                    "left_dark_ratio": round(left_dark_ratio, 4),
                    "left_edge_ratio": round(left_edge_ratio, 4),
                }
            )
            self._watchdog_reset()
            return True

        self._record(
            {
                "type": "vision_feature",
                "feature": "like_main_screen_recruit_button",
                "present": False,
                "source": "green_color_fallback",
                "region_x": x,
                "region_y": y,
                "region_width": width,
                "region_height": height,
                "green_ratio": round(green_ratio, 4),
                "bottom_dark_ratio": round(bottom_dark_ratio, 4),
                "bottom_bright_ratio": round(bottom_bright_ratio, 4),
                "bottom_edge_ratio": round(bottom_edge_ratio, 4),
                "left_dark_ratio": round(left_dark_ratio, 4),
                "left_edge_ratio": round(left_edge_ratio, 4),
                "rejected_reason": "main_ui_missing" if green_ratio > 0.08 else "green_missing",
            }
        )
        return False

    def detect_main_blocking_troop_prompt_in_image(
        self,
        image: np.ndarray,
    ) -> tuple[bool, dict[str, object], Point]:
        h, w = image.shape[:2]
        tap_point = Point(int(w * 0.74), int(h * 0.158))
        if w >= h:
            return False, {"reason": "not_portrait", "width": w, "height": h}, tap_point

        prompt_region = (
            int(w * 0.64),
            int(h * 0.13),
            int(w * 0.35),
            int(h * 0.10),
        )
        tab_region = (
            int(w * 0.66),
            int(h * 0.13),
            int(w * 0.17),
            int(h * 0.06),
        )

        px, py, pw, ph = prompt_region
        tx, ty, tw, th = tab_region
        prompt_crop = image[py : py + ph, px : px + pw]
        tab_crop = image[ty : ty + th, tx : tx + tw]
        if prompt_crop.size == 0 or tab_crop.size == 0:
            return False, {"reason": "empty_region"}, tap_point

        prompt_gray = cv2.cvtColor(prompt_crop, cv2.COLOR_BGR2GRAY)
        tab_gray = cv2.cvtColor(tab_crop, cv2.COLOR_BGR2GRAY)
        prompt_mean = float(prompt_gray.mean())
        prompt_dark_ratio = float((prompt_gray < 75).mean())
        prompt_edge_ratio = float((cv2.Canny(prompt_gray, 60, 120) > 0).mean())
        tab_bright_ratio = float((tab_gray > 150).mean())
        tab_edge_ratio = float((cv2.Canny(tab_gray, 60, 120) > 0).mean())

        present = (
            prompt_mean <= 105.0
            and prompt_dark_ratio >= 0.34
            and prompt_edge_ratio >= 0.055
            and tab_bright_ratio >= 0.035
            and tab_edge_ratio >= 0.075
        )
        metrics: dict[str, object] = {
            "present": present,
            "prompt_region_x": px,
            "prompt_region_y": py,
            "prompt_region_width": pw,
            "prompt_region_height": ph,
            "prompt_mean": round(prompt_mean, 1),
            "prompt_dark_ratio": round(prompt_dark_ratio, 4),
            "prompt_edge_ratio": round(prompt_edge_ratio, 4),
            "tab_bright_ratio": round(tab_bright_ratio, 4),
            "tab_edge_ratio": round(tab_edge_ratio, 4),
            "tap_x": tap_point.x if present else None,
            "tap_y": tap_point.y if present else None,
        }
        return present, metrics, tap_point

    def handle_main_blocking_troop_prompt_if_present(
        self,
        *,
        timeout_seconds: float = 0.8,
        max_taps: int = 2,
    ) -> bool:
        self._record(
            {
                "type": "state",
                "state": "handle_main_blocking_troop_prompt_if_present",
                "timeout_seconds": timeout_seconds,
                "max_taps": max_taps,
            }
        )
        handled_any = False
        deadline = time() + max(0.05, timeout_seconds)
        attempt = 0
        while attempt < max(1, max_taps):
            image = self.bot.screenshot_image()
            present, metrics, point = self.detect_main_blocking_troop_prompt_in_image(image)
            metrics.update({"type": "vision_feature", "feature": "main_blocking_troop_prompt", "attempt": attempt + 1})
            self._record(metrics)
            if not present:
                return handled_any

            self._save_image_snapshot("before_clear_main_blocking_troop_prompt", image)
            self.tap(
                f"点赞流程-处理部队编制引导({attempt + 1})",
                point,
                wait_seconds=self._fast_wait(1.2, 0.75),
            )
            self._record(
                {
                    "type": "keyevent",
                    "label": f"点赞流程-部队引导后安卓返回({attempt + 1})",
                    "keycode": 4,
                }
            )
            self.bot.client.keyevent(4)
            self._sleep_with_watchdog(self._fast_wait(1.0, 0.55), source="clear_main_blocking_troop_prompt_back")
            self.close_exit_confirm_if_present(timeout_seconds=self._fast_timeout(0.8, 0.25))
            handled_any = True
            attempt += 1
            if time() >= deadline:
                break

        self.screenshot("after_clear_main_blocking_troop_prompt")
        return handled_any

    def find_any_visible_back_button_in_image(
        self,
        image: np.ndarray,
    ) -> tuple[str | None, Match | None]:
        h, w = image.shape[:2]
        region = (0, int(h * 0.88), max(220, int(w * 0.34)), int(h * 0.12))
        candidates = (
            ("like_home_back_button", 0.70),
            ("like_friends_back_button", 0.70),
            ("gacha_recruit_page_back_button", 0.70),
            ("gacha_result_back_button", 0.70),
            ("alliance_back_button", 0.70),
            ("alliance_back_button_x2", 0.70),
            ("military_council_back_button", 0.70),
        )
        for candidate_key, threshold in candidates:
            button = self._find_template_in_image(
                image,
                candidate_key,
                threshold=threshold,
                region=region,
            )
            if button:
                return candidate_key, button
        return None, None

    def find_any_visible_back_button(self, *, timeout_seconds: float = 0.8) -> tuple[str | None, Match | None]:
        end_at = time() + max(0.0, timeout_seconds)
        while time() < end_at:
            image = self.bot.screenshot_image()
            candidate_key, button = self.find_any_visible_back_button_in_image(image)
            if button:
                return candidate_key, button
            remaining = end_at - time()
            if remaining <= 0:
                break
            self._sleep_with_watchdog(min(0.20, remaining), source="find_any_visible_back_button")
        return None, None

    def click_any_visible_back_if_present(self, *, timeout_seconds: float = 0.8) -> bool:
        self._record({"type": "state", "state": "click_any_visible_back_if_present"})
        candidate_key, button = self.find_any_visible_back_button(timeout_seconds=timeout_seconds)
        if button:
            point = Point(*button.center)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "visible_back_button",
                    "source": "template",
                    "template": candidate_key,
                    "x": button.x,
                    "y": button.y,
                    "width": button.width,
                    "height": button.height,
                    "score": round(button.score, 4),
                    "tap_x": point.x,
                    "tap_y": point.y,
                }
            )
            self.tap("异常矫正-点击可见返回", point, wait_seconds=1.4)
            return True

        self._record(
            {
                "type": "vision_feature",
                "feature": "visible_back_button",
                "source": "template",
                "present": False,
            }
        )
        return False

    def recover_to_main_screen(self, *, max_steps: int = 6) -> bool:
        self._record({"type": "state", "state": "recover_to_main_screen", "max_steps": max_steps})
        self.screenshot("before_recover_to_main_screen")
        for index in range(max(1, max_steps)):
            self._record(
                {
                    "type": "state",
                    "state": "recover_to_main_screen_step",
                    "step": index + 1,
                    "max_steps": max_steps,
                }
            )
            self.close_exit_confirm_if_present(timeout_seconds=0.4)
            self.close_known_retreat_if_present(timeout_seconds=0.4)
            if self.detect_like_main_screen():
                self.screenshot("after_recover_to_main_screen")
                return True

            if self.close_orange_card_detail_if_present(timeout_seconds=0.8):
                continue
            if self.skip_landscape_dialogs_if_present(max_taps=20, timeout_seconds=0.35):
                continue
            if self.skip_portrait_dialogs_if_present(max_taps=30, timeout_seconds=0.35):
                continue

            if self.click_any_visible_back_if_present(timeout_seconds=0.45):
                continue

            self._record(
                {
                    "type": "keyevent",
                    "label": "异常矫正-安卓返回兜底",
                    "keycode": 4,
                }
            )
            self.bot.client.keyevent(4)
            self._sleep_with_watchdog(1.0, source="recover_to_main_screen_key_back")
            self.close_exit_confirm_if_present(timeout_seconds=0.5)

        recovered = self.detect_like_main_screen()
        self.screenshot("after_recover_to_main_screen" if recovered else "recover_to_main_screen_failed")
        return recovered

    @staticmethod
    def _find_red_dot(image: np.ndarray, region: tuple[int, int, int, int]) -> Match | None:
        x, y, width, height = region
        img_h, img_w = image.shape[:2]
        x = max(0, min(x, img_w - 1))
        y = max(0, min(y, img_h - 1))
        width = max(1, min(width, img_w - x))
        height = max(1, min(height, img_h - y))
        crop = image[y : y + height, x : x + width]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        low_red = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([12, 255, 255]))
        high_red = cv2.inRange(hsv, np.array([168, 70, 70]), np.array([180, 255, 255]))
        mask = cv2.bitwise_or(low_red, high_red)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates: list[Match] = []
        for contour in contours:
            area = float(cv2.contourArea(contour))
            box_x, box_y, box_w, box_h = cv2.boundingRect(contour)
            if area >= 40 and 6 <= box_w <= 42 and 6 <= box_h <= 42:
                candidates.append(
                    Match(
                        x=int(x + box_x),
                        y=int(y + box_y),
                        width=int(box_w),
                        height=int(box_h),
                        score=area,
                        kind="red_dot",
                    )
                )
        if not candidates:
            return None
        return max(candidates, key=lambda item: item.score)

    def open_recruit_if_red_dot_for_gacha(self, *, allow_without_red_dot: bool = False) -> Path:
        self._record({"type": "state", "state": "open_recruit_if_red_dot_for_gacha"})
        self.screenshot("before_gacha_open_recruit_if_red_dot")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button_region = (int(w * 0.78), int(h * 0.86), int(w * 0.22), int(h * 0.14))
        recruit = self._find_template_in_image(
            image,
            "main_recruit_button",
            threshold=0.68,
            region=button_region,
        )
        if not recruit and not self.fast_mode:
            recruit = self.wait_for_template(
                "抽卡流程-主界面招募按钮",
                "main_recruit_button",
                timeout_seconds=1.2,
                threshold=0.68,
                region=button_region,
            )

        if recruit:
            point = Point(*recruit.center)
            source = "template"
        else:
            self.screenshot("gacha_recruit_button_not_found")
            raise RuntimeError("Gacha flow expected main recruit button, but it was not found.")

        self._record(
            {
                "type": "vision_feature",
                "feature": "gacha_recruit_button",
                "source": source,
                "x": recruit.x,
                "y": recruit.y,
                "width": recruit.width,
                "height": recruit.height,
                "score": round(recruit.score, 4),
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )

        red_region = (
            max(0, recruit.x + int(recruit.width * 0.45)),
            max(0, recruit.y + int(recruit.height * 0.10)),
            min(w - recruit.x, int(recruit.width * 0.45)),
            min(h - recruit.y, int(recruit.height * 0.35)),
        )
        red_dot = self._find_red_dot(image, red_region)
        self._record(
            {
                "type": "vision_feature",
                "feature": "gacha_recruit_red_dot",
                "present": red_dot is not None,
                "region_x": red_region[0],
                "region_y": red_region[1],
                "region_width": red_region[2],
                "region_height": red_region[3],
                "x": red_dot.x if red_dot else None,
                "y": red_dot.y if red_dot else None,
                "width": red_dot.width if red_dot else None,
                "height": red_dot.height if red_dot else None,
                "score": round(red_dot.score, 1) if red_dot else 0.0,
            }
        )
        if not red_dot:
            self.screenshot("gacha_recruit_red_dot_not_found")
            if not allow_without_red_dot:
                raise RuntimeError("Gacha flow expected a red dot on the recruit button, but none was found.")
            self._record(
                {
                    "type": "state",
                    "state": "gacha_open_without_red_dot",
                    "reason": "check_half_price_after_free_already_done",
                }
            )

        label = "抽卡流程-无红点进入招募检查半价" if red_dot is None else "抽卡流程-点击招募按钮"
        self.tap(label, point, wait_seconds=self._fast_wait(1.8, 1.0))
        return self.screenshot("after_gacha_open_recruit_if_red_dot")

    def select_named_pack_for_gacha(self, max_swipes: int = 5) -> Path:
        self._record(
            {
                "type": "state",
                "state": "select_named_pack_for_gacha",
                "max_swipes": max_swipes,
            }
        )
        self.screenshot("before_gacha_select_named_pack")

        for attempt in range(max_swipes + 1):
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]
            pack_region = (0, int(h * 0.72), w, int(h * 0.14))
            named_pack = self.wait_for_template(
                "抽卡流程-名将卡包",
                "gacha_named_pack_tab",
                timeout_seconds=self._fast_timeout(0.8, 0.35),
                threshold=0.72,
                region=pack_region,
            )
            if named_pack:
                point = Point(*named_pack.center)
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "gacha_named_pack_tab",
                        "source": "template",
                        "attempt": attempt,
                        "x": named_pack.x,
                        "y": named_pack.y,
                        "width": named_pack.width,
                        "height": named_pack.height,
                        "score": round(named_pack.score, 4),
                        "tap_x": point.x,
                        "tap_y": point.y,
                    }
                )
                self.tap("抽卡流程-点击名将卡包", point, wait_seconds=self._fast_wait(1.2, 0.75))
                return self.screenshot("after_gacha_select_named_pack")

            if attempt >= max_swipes:
                break

            start = Point(int(w * 0.84), int(h * 0.80))
            end = Point(int(w * 0.18), int(h * 0.80))
            self._record(
                {
                    "type": "swipe",
                    "label": "抽卡流程-卡包栏左滑查找名将",
                    "attempt": attempt + 1,
                    "x1": start.x,
                    "y1": start.y,
                    "x2": end.x,
                    "y2": end.y,
                    "duration_ms": 360,
                }
            )
            self.bot.swipe(start.x, start.y, end.x, end.y, 360)
            self._sleep_with_watchdog(self._fast_wait(0.6, 0.35), source="gacha_named_pack_swipe")
            self.screenshot(f"gacha_named_pack_swipe_{attempt + 1:02d}")

        self.screenshot("gacha_named_pack_not_found")
        raise RuntimeError("Gacha flow could not find the named-card pack after swiping left.")

    def click_free_recruit_once_for_gacha(self) -> Path:
        self._record({"type": "state", "state": "click_free_recruit_once_for_gacha"})
        self.screenshot("before_gacha_click_free_recruit_once")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button = self.wait_for_template(
            "抽卡流程-招募1次按钮",
            "gacha_recruit_once_button",
            timeout_seconds=self._fast_timeout(1.2, 0.55),
            threshold=0.74,
            region=(int(w * 0.08), int(h * 0.58), int(w * 0.42), int(h * 0.16)),
        )
        if not button:
            self.screenshot("gacha_recruit_once_button_not_found")
            raise RuntimeError("Gacha flow could not find the recruit-once button.")

        free_region = (
            max(0, button.x + int(button.width * 0.80)),
            max(0, button.y - int(button.height * 0.18)),
            min(w - button.x, int(button.width * 0.46)),
            min(h - button.y, int(button.height * 1.35)),
        )
        free_badge = self._find_template_in_image(
            image,
            "gacha_recruit_once_free_badge",
            threshold=0.70,
            region=free_region,
        )
        half_badge = self._find_template_in_image(
            image,
            "gacha_recruit_once_half_badge",
            threshold=0.70,
            region=free_region,
        )
        free_badge_wins = free_badge is not None and (
            half_badge is None or free_badge.score >= half_badge.score + 0.025
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "gacha_recruit_once_button",
                "source": "template",
                "x": button.x,
                "y": button.y,
                "width": button.width,
                "height": button.height,
                "score": round(button.score, 4),
            }
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "gacha_recruit_once_free_badge",
                "present": free_badge is not None,
                "region_x": free_region[0],
                "region_y": free_region[1],
                "region_width": free_region[2],
                "region_height": free_region[3],
                "x": free_badge.x if free_badge else None,
                "y": free_badge.y if free_badge else None,
                "width": free_badge.width if free_badge else None,
                "height": free_badge.height if free_badge else None,
                "score": round(free_badge.score, 4) if free_badge else 0.0,
                "half_badge_score": round(half_badge.score, 4) if half_badge else 0.0,
                "classification": "free" if free_badge_wins else "half_or_missing",
            }
        )
        if not free_badge_wins:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "gacha_free_badge_rejected",
                    "reason": "half_price_badge_won" if half_badge else "free_badge_missing",
                    "free_score": round(free_badge.score, 4) if free_badge else 0.0,
                    "half_score": round(half_badge.score, 4) if half_badge else 0.0,
                }
            )
            self.screenshot("gacha_recruit_once_free_badge_not_found")
            raise RuntimeError("Gacha flow found recruit-once, but the free badge was not present or was half-price.")

        point = Point(*button.center)
        self.tap("抽卡流程-点击免费招募1次", point, wait_seconds=self._fast_wait(2.5, 1.8))
        return self.screenshot("after_gacha_click_free_recruit_once")

    def back_from_recruit_result_for_gacha(self) -> Path:
        self._record({"type": "state", "state": "back_from_recruit_result_for_gacha"})
        self.screenshot("before_gacha_back_from_recruit_result")

        branch = "unknown"
        button = None
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        back_region = (0, int(h * 0.90), int(w * 0.30), int(h * 0.10))

        for attempt in range(1, 7):
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]
            back_region = (0, int(h * 0.90), int(w * 0.30), int(h * 0.10))
            button = self._find_template_in_image(
                image,
                "gacha_result_back_button",
                threshold=0.70,
                region=back_region,
            )
            if button:
                if branch != "orange_card":
                    branch = "normal_result"
                break

            orange_page, orange_metrics = self.detect_orange_card_effect_page(image)
            orange_arrow = self.find_orange_card_down_arrow(image) if orange_page else None
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "gacha_recruit_result_branch",
                    "attempt": attempt,
                    "branch": "orange_card" if orange_page else "pending",
                    "orange_present": orange_page,
                    "orange_arrow_present": orange_arrow is not None,
                    "screen_dark_ratio": round(orange_metrics["screen_dark_ratio"], 3),
                    "lower_dark_ratio": round(orange_metrics["lower_dark_ratio"], 3),
                    "portrait_edge_ratio": round(orange_metrics["portrait_edge_ratio"], 4),
                }
            )
            if orange_page:
                branch = "orange_card"
                orange_skipped = self.skip_orange_card_effect_if_present(
                    timeout_seconds=self._fast_timeout(5.0, 3.0)
                )
                detail_closed = self.close_orange_card_detail_if_present(
                    timeout_seconds=self._fast_timeout(3.0, 1.2)
                )
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "gacha_orange_card_result_handled",
                        "attempt": attempt,
                        "skipped": orange_skipped,
                        "detail_closed": detail_closed,
                    }
                )
                continue

            showcase_advanced = self.advance_gacha_showcase_if_present(
                timeout_seconds=self._fast_timeout(1.8, 0.8)
            )
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "gacha_optional_showcase_continue",
                    "stage": f"before_back_button_retry_{attempt}",
                    "advanced": showcase_advanced,
                }
            )
            if showcase_advanced:
                branch = "orange_card"
                continue

            if attempt < 3:
                self._sleep_with_watchdog(0.45, source="gacha_result_settle")
                continue

            # The ordinary result page always returns through the lower-left button.
            # Use its stable relative position when an animation obscures the template.
            branch = "normal_result"
            break

        if button:
            point = Point(
                button.x + button.width // 2,
                min(h - 12, button.y + int(button.height * 0.90)),
            )
            source = "template"
            button_fields = {
                "x": button.x,
                "y": button.y,
                "width": button.width,
                "height": button.height,
                "score": round(button.score, 4),
            }
        else:
            point = Point(int(w * 0.155), int(h * 0.968))
            source = "coordinate_fallback"
            button_fields = {"score": 0.0}

        self._record(
            {
                "type": "vision_feature",
                "feature": "gacha_result_back_button",
                "branch": branch,
                "source": source,
                **button_fields,
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        label = "抽卡流程-橙卡处理后点击左下返回" if branch == "orange_card" else "抽卡流程-普通结果点击左下返回"
        self.tap(label, point, wait_seconds=self._fast_wait(1.5, 0.9))
        return self.screenshot("after_gacha_back_from_recruit_result")

    def back_from_recruit_page_for_gacha(self) -> Path:
        self._record({"type": "state", "state": "back_from_recruit_page_for_gacha"})
        self.screenshot("before_gacha_back_from_recruit_page")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        for attempt in range(1, 7):
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]
            if self.detect_like_main_screen():
                self._record(
                    {
                        "type": "state",
                        "state": "gacha_back_from_recruit_page_already_main",
                        "attempt": attempt,
                    }
                )
                return self.screenshot("after_gacha_back_from_recruit_page_already_main")

            if w < h:
                overlay = image[int(h * 0.50) : int(h * 0.70), int(w * 0.25) : int(w * 0.98)]
                overlay_gray = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
                overlay_mean = float(overlay_gray.mean())
                overlay_dark_ratio = float((overlay_gray < 70).mean())
                continue_icon = self._find_template_in_image(
                    image,
                    "dialog_continue_icon",
                    threshold=0.45,
                    region=(int(w * 0.76), int(h * 0.50), int(w * 0.24), int(h * 0.32)),
                )
                if overlay_mean <= 92 and overlay_dark_ratio >= 0.45 and continue_icon:
                    point = Point(*continue_icon.center)
                    self._record(
                        {
                            "type": "vision_feature",
                            "feature": "gacha_return_dialog_continue",
                            "attempt": attempt,
                            "overlay_mean": round(overlay_mean, 1),
                            "overlay_dark_ratio": round(overlay_dark_ratio, 3),
                            "x": continue_icon.x,
                            "y": continue_icon.y,
                            "width": continue_icon.width,
                            "height": continue_icon.height,
                            "score": round(continue_icon.score, 4),
                            "tap_x": point.x,
                            "tap_y": point.y,
                        }
                    )
                    self.tap(
                        f"抽卡流程-返回时推进武将展示#{attempt}",
                        point,
                        wait_seconds=self._fast_wait(1.8, 1.0),
                    )
                    continue

            button = self._find_template_in_image(
                image,
                "gacha_recruit_page_back_button",
                threshold=0.66,
                region=(0, int(h * 0.90), int(w * 0.30), int(h * 0.10)),
            )
            if button:
                point = Point(
                    button.x + button.width // 2,
                    min(h - 12, button.y + int(button.height * 0.90)),
                )
                source = "template"
                button_fields = {
                    "x": button.x,
                    "y": button.y,
                    "width": button.width,
                    "height": button.height,
                    "score": round(button.score, 4),
                }
            else:
                point = Point(int(w * 0.155), int(h * 0.968))
                source = "coordinate_fallback"
                button_fields = {"score": 0.0}

            result_back = self._find_template_in_image(
                image,
                "gacha_result_back_button",
                threshold=0.66,
                region=(0, int(h * 0.90), int(w * 0.30), int(h * 0.10)),
            )
            if result_back:
                point = Point(
                    result_back.x + result_back.width // 2,
                    min(h - 12, result_back.y + int(result_back.height * 0.90)),
                )
                source = "result_template_fallback"
                button_fields = {
                    "x": result_back.x,
                    "y": result_back.y,
                    "width": result_back.width,
                    "height": result_back.height,
                    "score": round(result_back.score, 4),
                }

            self._record(
                {
                    "type": "vision_feature",
                    "feature": "gacha_recruit_page_back_button",
                    "attempt": attempt,
                    "source": source,
                    **button_fields,
                    "tap_x": point.x,
                    "tap_y": point.y,
                }
            )
            self.tap(
                f"抽卡流程-点击招募页左下返回#{attempt}",
                point,
                wait_seconds=self._fast_wait(1.8, 1.0),
            )
            if self.detect_like_main_screen():
                return self.screenshot("after_gacha_back_from_recruit_page")
            self.close_exit_confirm_if_present(timeout_seconds=0.35)

        recovered = self.recover_to_main_screen(max_steps=10)
        self._record(
            {
                "type": "state",
                "state": "gacha_back_from_recruit_page_recovery",
                "recovered": recovered,
            }
        )
        if recovered:
            return self.screenshot("after_gacha_back_from_recruit_page_recovery")

        self._finish_black_screen_watchdog_if_active(
            source="gacha_back_from_recruit_page_failure"
        )
        self.screenshot("gacha_recruit_page_back_button_not_found")
        raise RuntimeError("Gacha flow could not return from the recruit page to the main screen.")

    def run_free_gacha_if_available(self) -> bool:
        self._record({"type": "state", "state": "run_free_gacha_if_available"})
        try:
            self.open_recruit_if_red_dot_for_gacha(allow_without_red_dot=True)
        except RuntimeError as exc:
            message = str(exc)
            if "main recruit button" not in message:
                raise
            self._record(
                {
                    "type": "state",
                    "state": "free_gacha_skipped",
                    "reason": "recruit_button_missing",
                }
            )
            return False

        self.select_named_pack_for_gacha()
        free_done = False
        try:
            self.click_free_recruit_once_for_gacha()
        except RuntimeError as exc:
            if "free badge" not in str(exc):
                raise
            self._record(
                {
                    "type": "state",
                    "state": "free_gacha_skipped",
                    "reason": "free_badge_missing",
                }
            )
        else:
            free_done = True
            self.back_from_recruit_result_for_gacha()

        half_done = self.click_half_recruit_once_for_gacha_if_available()
        self._record(
            {
                "type": "vision_feature",
                "feature": "gacha_half_recruit_once",
                "done": half_done,
            }
        )
        if half_done:
            self.back_from_recruit_result_for_gacha()
        self.back_from_recruit_page_for_gacha()
        return free_done or half_done

    def click_half_recruit_once_for_gacha_if_available(self) -> bool:
        self._record({"type": "state", "state": "click_half_recruit_once_for_gacha_if_available"})
        self.screenshot("before_gacha_click_half_recruit_once")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button_region = (int(w * 0.14), int(h * 0.61), int(w * 0.34), int(h * 0.10))
        badge_region = (int(w * 0.36), int(h * 0.60), int(w * 0.13), int(h * 0.12))

        badge = self.wait_for_template(
            "抽卡流程-半价角标",
            "gacha_recruit_once_half_badge",
            timeout_seconds=self._fast_timeout(1.6, 0.7),
            threshold=0.70,
            region=badge_region,
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "gacha_half_badge",
                "present": badge is not None,
                "x": badge.x if badge else None,
                "y": badge.y if badge else None,
                "width": badge.width if badge else None,
                "height": badge.height if badge else None,
                "score": round(badge.score, 4) if badge else 0.0,
            }
        )
        if not badge:
            self.screenshot("gacha_half_badge_not_found")
            return False

        button = self.wait_for_template(
            "抽卡流程-半价招募1次按钮",
            "gacha_recruit_once_half_button",
            timeout_seconds=self._fast_timeout(1.2, 0.5),
            threshold=0.68,
            region=button_region,
        )
        if button:
            point = Point(button.x + int(button.width * 0.48), button.y + button.height // 2)
            source = "template"
            button_fields = {
                "x": button.x,
                "y": button.y,
                "width": button.width,
                "height": button.height,
                "score": round(button.score, 4),
            }
        else:
            point = Point(int(w * 0.304), int(h * 0.653))
            source = "coordinate_fallback"
            button_fields = {"score": 0.0}

        self._record(
            {
                "type": "vision_feature",
                "feature": "gacha_half_recruit_once_button",
                "source": source,
                "badge_x": badge.x,
                "badge_y": badge.y,
                **button_fields,
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("抽卡流程-点击半价招募1次", point, wait_seconds=self._fast_wait(2.0, 1.2))
        self.screenshot("after_gacha_click_half_recruit_once")
        return True

    def _tap_sgzz_template_or_fallback(
        self,
        *,
        label: str,
        feature: str,
        template_key: str,
        threshold: float,
        region: tuple[int, int, int, int],
        timeout_seconds: float,
        wait_seconds: float,
        fallback: Point | None = None,
        tap_point_for_match: Callable[[Match], Point] | None = None,
        required: bool = False,
    ) -> bool:
        match = self.wait_for_template(
            label,
            template_key,
            timeout_seconds=timeout_seconds,
            threshold=threshold,
            region=region,
        )
        if match:
            point = tap_point_for_match(match) if tap_point_for_match else Point(*match.center)
            source = "template"
            match_fields = {
                "x": match.x,
                "y": match.y,
                "width": match.width,
                "height": match.height,
                "score": round(match.score, 4),
            }
        elif fallback is not None:
            point = fallback
            source = "coordinate_fallback"
            match_fields = {"score": 0.0}
        else:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": feature,
                    "present": False,
                    "source": "not_found",
                    "threshold": threshold,
                    "region": list(region),
                }
            )
            if required:
                self.screenshot(f"{feature}_not_found")
                raise RuntimeError(f"SGZZ game circle sign-in could not find {feature}.")
            return False

        self._record(
            {
                "type": "vision_feature",
                "feature": feature,
                "present": match is not None,
                "source": source,
                "threshold": threshold,
                "region": list(region),
                **match_fields,
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap(label, point, wait_seconds=wait_seconds)
        return match is not None

    def open_gamecircle_for_signin(self) -> Path:
        self._record({"type": "state", "state": "open_gamecircle_for_signin"})
        self.screenshot("before_gamecircle_open_social")

        if not self.detect_like_main_screen():
            recovered = self.recover_to_main_screen(max_steps=6)
            self._record(
                {
                    "type": "state",
                    "state": "gamecircle_recover_before_open_social",
                    "recovered": recovered,
                }
            )
            if not recovered:
                self.screenshot("gamecircle_main_screen_not_ready")
                raise RuntimeError("Game circle sign-in expected main screen before opening 社.")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (int(w * 0.28), int(h * 0.10), int(w * 0.30), int(h * 0.12))
        fallback = Point(int(w * 0.41), int(h * 0.16))
        self._tap_sgzz_template_or_fallback(
            label="游戏圈签到-点击社",
            feature="gamecircle_social_button",
            template_key="main_social_button",
            threshold=0.68,
            region=region,
            timeout_seconds=self._fast_timeout(1.8, 0.8),
            wait_seconds=self._fast_wait(3.0, 1.8),
            fallback=fallback,
            required=True,
        )
        return self.screenshot("after_gamecircle_open_social")

    def open_gamecircle_signin_welfare(self) -> Path:
        self._record({"type": "state", "state": "open_gamecircle_signin_welfare"})
        self.screenshot("before_gamecircle_signin_welfare")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (0, int(h * 0.07), int(w * 0.34), int(h * 0.18))
        fallback = Point(int(w * 0.092), int(h * 0.125))
        self._tap_sgzz_template_or_fallback(
            label="游戏圈签到-点击签到福利",
            feature="gamecircle_signin_welfare_button",
            template_key="gamecircle_signin_welfare_button",
            threshold=0.68,
            region=region,
            timeout_seconds=self._fast_timeout(5.0, 3.0),
            wait_seconds=self._fast_wait(2.5, 1.6),
            fallback=fallback,
            tap_point_for_match=lambda match: Point(
                match.x + match.width // 2,
                match.y + max(4, int(match.height * 0.35)),
            ),
            required=True,
        )
        return self.screenshot("after_gamecircle_signin_welfare")

    def click_gamecircle_pending_claim_label(self) -> bool:
        self._record({"type": "state", "state": "click_gamecircle_pending_claim_label"})
        self.screenshot("before_gamecircle_pending_claim")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (0, int(h * 0.30), w, int(h * 0.55))
        clicked = self._tap_sgzz_template_or_fallback(
            label="游戏圈签到-点击待领取/待签到标签",
            feature="gamecircle_pending_claim_label",
            template_key="gamecircle_pending_claim_label",
            threshold=0.68,
            region=region,
            timeout_seconds=self._fast_timeout(4.0, 2.5),
            wait_seconds=self._fast_wait(1.6, 1.0),
            required=False,
        )
        if not clicked:
            self._record(
                {
                    "type": "state",
                    "state": "gamecircle_pending_claim_missing_assume_already_signed",
                    "reason": "pending_claim_label_not_found",
                }
            )
            self.screenshot("gamecircle_pending_claim_label_not_found")
            return False
        self.screenshot("after_gamecircle_pending_claim")
        return True

    def confirm_gamecircle_signin_success_if_present(self, *, expected: bool) -> bool:
        self._record(
            {
                "type": "state",
                "state": "confirm_gamecircle_signin_success_if_present",
                "expected": expected,
            }
        )
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (int(w * 0.16), int(h * 0.54), int(w * 0.68), int(h * 0.16))
        fallback = Point(int(w * 0.50), int(h * 0.614)) if expected else None
        confirmed = self._tap_sgzz_template_or_fallback(
            label="游戏圈签到-点击确定",
            feature="gamecircle_signin_success_confirm_button",
            template_key="gamecircle_signin_success_confirm_button",
            threshold=0.68,
            region=region,
            timeout_seconds=self._fast_timeout(3.0, 2.0),
            wait_seconds=self._fast_wait(1.2, 0.8),
            fallback=fallback,
            required=False,
        )
        if confirmed or fallback is not None:
            self.screenshot("after_gamecircle_signin_confirm")
            return True
        return False

    def exit_gamecircle_for_signin(self) -> Path:
        self._record({"type": "state", "state": "exit_gamecircle_for_signin"})
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (int(w * 0.78), 0, int(w * 0.22), int(h * 0.08))
        fallback = Point(int(w * 0.905), int(h * 0.034))
        self._tap_sgzz_template_or_fallback(
            label="游戏圈签到-点击退出",
            feature="gamecircle_exit_button",
            template_key="gamecircle_exit_button",
            threshold=0.66,
            region=region,
            timeout_seconds=self._fast_timeout(2.0, 1.2),
            wait_seconds=self._fast_wait(2.0, 1.2),
            fallback=fallback,
            required=True,
        )

        for attempt in range(1, 4):
            if self.detect_like_main_screen():
                return self.screenshot("after_gamecircle_exit")
            self._record(
                {
                    "type": "state",
                    "state": "gamecircle_exit_not_main_retry",
                    "attempt": attempt,
                }
            )
            self.bot.client.keyevent(4)
            self._sleep_with_watchdog(1.0, source=f"gamecircle_exit_key_back:{attempt}")

        self.screenshot("gamecircle_exit_not_main")
        raise RuntimeError("Game circle sign-in could not return to the main screen after exit.")

    def run_gamecircle_signin(self) -> Path:
        self._record({"type": "state", "state": "run_gamecircle_signin"})
        self.screenshot("before_gamecircle_signin")

        opened_gamecircle = False
        claimed = False
        confirmed = False
        already_signed = False
        try:
            self.open_gamecircle_for_signin()
            opened_gamecircle = True
            self.open_gamecircle_signin_welfare()
            claimed = self.click_gamecircle_pending_claim_label()
            if claimed:
                confirmed = self.confirm_gamecircle_signin_success_if_present(expected=True)
            else:
                already_signed = True
        finally:
            if opened_gamecircle:
                exit_path = self.exit_gamecircle_for_signin()
            else:
                exit_path = self.screenshot("after_gamecircle_signin_not_opened")

        self._record(
            {
                "type": "vision_feature",
                "feature": "gamecircle_signin",
                "done": claimed or already_signed,
                "claimed": claimed,
                "confirmed": confirmed,
                "already_signed": already_signed,
            }
        )
        return exit_path

    def detect_recent_login_account_chooser(self, image: np.ndarray | None = None) -> bool:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            return False

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        full_bright_ratio = float((gray > 235).mean()) if gray.size else 0.0

        modal_region = (int(w * 0.05), int(h * 0.28), int(w * 0.90), int(h * 0.43))
        x, y, width, height = self._clip_region(image, modal_region)
        modal = gray[y : y + height, x : x + width]
        bright_ratio = float((modal > 220).mean()) if modal.size else 0.0

        blue_region = (int(w * 0.10), int(h * 0.52), int(w * 0.80), int(h * 0.10))
        bx, by, bw, bh = self._clip_region(image, blue_region)
        blue_crop = image[by : by + bh, bx : bx + bw]
        hsv = cv2.cvtColor(blue_crop, cv2.COLOR_BGR2HSV)
        blue_mask = cv2.inRange(hsv, np.array([95, 60, 120]), np.array([125, 255, 255]))
        blue_ratio = float((blue_mask > 0).mean()) if blue_mask.size else 0.0

        arrow_region = (int(w * 0.76), int(h * 0.38), int(w * 0.12), int(h * 0.20))
        ax, ay, aw, ah = self._clip_region(image, arrow_region)
        arrow_crop = gray[ay : ay + ah, ax : ax + aw]
        dark_ratio = float((arrow_crop < 90).mean()) if arrow_crop.size else 0.0

        present = bright_ratio > 0.58 and blue_ratio < 0.12 and dark_ratio > 0.006
        if present:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_recent_login_chooser",
                    "present": True,
                    "full_bright_ratio": round(full_bright_ratio, 4),
                    "bright_ratio": round(bright_ratio, 4),
                    "blue_button_ratio": round(blue_ratio, 4),
                    "arrow_dark_ratio": round(dark_ratio, 4),
                }
            )
            return True

        title_marker = self._find_template_in_image(
            image,
            "title_select_server",
            threshold=0.70,
            region=(int(w * 0.48), int(h * 0.76), int(w * 0.32), int(h * 0.10)),
        ) or self._find_template_in_image(
            image,
            "title_enter_button",
            threshold=0.70,
            region=(int(w * 0.20), int(h * 0.72), int(w * 0.60), int(h * 0.14)),
        )
        if title_marker is not None:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_recent_login_chooser",
                    "present": False,
                    "reason": "title_screen_visible",
                    "full_bright_ratio": round(full_bright_ratio, 4),
                    "title_x": title_marker.x,
                    "title_y": title_marker.y,
                    "title_score": round(title_marker.score, 4),
                }
            )
            return False

        if full_bright_ratio > 0.62:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_recent_login_chooser",
                    "present": False,
                    "reason": "full_bright_non_game_surface",
                    "full_bright_ratio": round(full_bright_ratio, 4),
                }
            )
            return False
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_recent_login_chooser",
                "present": present,
                "full_bright_ratio": round(full_bright_ratio, 4),
                "bright_ratio": round(bright_ratio, 4),
                "blue_button_ratio": round(blue_ratio, 4),
                "arrow_dark_ratio": round(dark_ratio, 4),
            }
        )
        return present

    def detect_login_secondary_confirm_button(self, image: np.ndarray | None = None) -> Match | None:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_login_secondary_confirm",
                    "present": False,
                    "reason": "landscape_screen",
                }
            )
            return None

        login_modal = self._find_template_in_image(
            image,
            "account_login_modal_logo",
            threshold=0.72,
            region=(int(w * 0.24), int(h * 0.28), int(w * 0.52), int(h * 0.22)),
        )
        login_button = self._find_template_in_image(
            image,
            "account_login_button",
            threshold=0.74,
            region=(int(w * 0.08), int(h * 0.50), int(w * 0.84), int(h * 0.18)),
        )
        if login_modal or login_button:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_login_secondary_confirm",
                    "present": False,
                    "reason": "primary_login_modal_visible",
                    "login_modal_score": round(login_modal.score, 4) if login_modal else 0.0,
                    "login_button_score": round(login_button.score, 4) if login_button else 0.0,
                }
            )
            return None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        panel_region = (int(w * 0.08), int(h * 0.30), int(w * 0.84), int(h * 0.42))
        px, py, pw, ph = self._clip_region(image, panel_region)
        panel_gray = gray[py : py + ph, px : px + pw]
        panel_bright_ratio = float((panel_gray > 220).mean()) if panel_gray.size else 0.0
        panel_text_ratio = float(((panel_gray > 35) & (panel_gray < 180)).mean()) if panel_gray.size else 0.0

        button_region = (int(w * 0.16), int(h * 0.47), int(w * 0.72), int(h * 0.24))
        bx, by, bw, bh = self._clip_region(image, button_region)
        button_crop = image[by : by + bh, bx : bx + bw]
        hsv = cv2.cvtColor(button_crop, cv2.COLOR_BGR2HSV)
        blue_mask = cv2.inRange(hsv, np.array([95, 55, 105]), np.array([126, 255, 255]))
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        blue_ratio = float((blue_mask > 0).mean()) if blue_mask.size else 0.0

        min_area = max(220, int(w * h * 0.00025))
        candidates: list[Match] = []
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < min_area:
                continue
            x, y, width, height = cv2.boundingRect(contour)
            if not (36 <= width <= int(w * 0.62) and 18 <= height <= 88):
                continue
            absolute_x = int(bx + x)
            absolute_y = int(by + y)
            if not (int(h * 0.48) <= absolute_y + height // 2 <= int(h * 0.72)):
                continue
            candidates.append(
                Match(
                    x=absolute_x,
                    y=absolute_y,
                    width=int(width),
                    height=int(height),
                    score=area,
                    kind="color",
                )
            )

        button = max(candidates, key=lambda item: (item.x + item.width // 2, item.score), default=None)
        present = button is not None and panel_bright_ratio > 0.36 and panel_text_ratio > 0.025 and blue_ratio > 0.004
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_login_secondary_confirm",
                "present": present,
                "panel_bright_ratio": round(panel_bright_ratio, 4),
                "panel_text_ratio": round(panel_text_ratio, 4),
                "blue_button_ratio": round(blue_ratio, 4),
                "candidate_count": len(candidates),
                "button_x": button.x if button else None,
                "button_y": button.y if button else None,
                "button_width": button.width if button else None,
                "button_height": button.height if button else None,
                "button_area": round(button.score, 2) if button else 0.0,
            }
        )
        return button if present else None

    def click_login_secondary_confirm_if_present(self, *, timeout_seconds: float = 1.0) -> bool:
        self._record({"type": "state", "state": "click_login_secondary_confirm_if_present"})
        end_at = time() + max(0.1, timeout_seconds)
        while time() < end_at:
            image = self.bot.screenshot_image()
            if self._recover_external_foreground_if_needed(
                source="click_login_secondary_confirm_if_present",
                image=image,
            ):
                continue
            button = self.detect_login_secondary_confirm_button(image)
            if button:
                point = Point(*button.center)
                self._save_image_snapshot("before_account_login_secondary_confirm", image)
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_login_secondary_confirm_button",
                        "source": "blue_primary_button",
                        "x": button.x,
                        "y": button.y,
                        "width": button.width,
                        "height": button.height,
                        "area": round(button.score, 2),
                        "tap_x": point.x,
                        "tap_y": point.y,
                    }
                )
                self.tap("账号登录二次确认-点击主按钮", point, wait_seconds=2.0)
                self.screenshot("after_account_login_secondary_confirm")
                return True
            self._sleep_with_watchdog(0.2, source="click_login_secondary_confirm_if_present")
        return False

    def detect_recent_login_submit_button(self, image: np.ndarray) -> Match | None:
        h, w = image.shape[:2]
        if w >= h:
            return None

        region = (int(w * 0.08), int(h * 0.61), int(w * 0.84), int(h * 0.12))
        x0, y0, rw, rh = self._clip_region(image, region)
        crop = image[y0 : y0 + rh, x0 : x0 + rw]
        if crop.size == 0:
            return None

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([95, 55, 120]), np.array([125, 255, 255]))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

        min_area = max(3600, int(w * h * 0.006))
        candidates: list[Match] = []
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < min_area:
                continue
            x, y, width, height = cv2.boundingRect(contour)
            if width < int(w * 0.45) or height < 42:
                continue
            absolute_x = int(x0 + x)
            absolute_y = int(y0 + y)
            center_y = absolute_y + height // 2
            if not (int(h * 0.62) <= center_y <= int(h * 0.72)):
                continue
            candidates.append(
                Match(
                    x=absolute_x,
                    y=absolute_y,
                    width=int(width),
                    height=int(height),
                    score=area,
                    kind="color",
                )
            )

        button = max(candidates, key=lambda item: item.score, default=None)
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_recent_login_submit_button",
                "present": button is not None,
                "source": "blue_button_color",
                "candidate_count": len(candidates),
                "x": button.x if button else None,
                "y": button.y if button else None,
                "width": button.width if button else None,
                "height": button.height if button else None,
                "area": round(button.score, 2) if button else 0.0,
                "tap_x": button.center[0] if button else None,
                "tap_y": button.center[1] if button else None,
            }
        )
        return button

    def _classify_login_captcha_target(self, image: np.ndarray, box: tuple[int, int, int, int]) -> str:
        x, y, width, height = box
        crop = image[y : y + height, x : x + width]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        purple_ratio = float(
            (((hsv[:, :, 0] > 120) & (hsv[:, :, 0] < 170) & (hsv[:, :, 1] > 40))).mean()
        )
        mask = ((gray < 245).astype("uint8")) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        components = [contour for contour in contours if cv2.contourArea(contour) > 5]
        area = sum(float(cv2.contourArea(contour)) for contour in components)
        density = area / float(max(1, width * height))
        if purple_ratio >= 0.08:
            return "purple_flower"
        if len(components) >= 3 and density <= 0.38:
            return "segmented_circle"
        return "skull"

    def _detect_login_captcha_order(self, image: np.ndarray) -> list[str]:
        h, w = image.shape[:2]
        x1, y1, width, height = (
            int(w * 0.58),
            int(h * 0.37),
            int(w * 0.25),
            int(h * 0.05),
        )
        crop = image[y1 : y1 + height, x1 : x1 + width]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        mask = ((gray < 245).astype("uint8")) * 255
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes: list[tuple[int, int, int, int]] = []
        for contour in contours:
            x, y, bw, bh = cv2.boundingRect(contour)
            area = float(cv2.contourArea(contour))
            if area < 90 or not (14 <= bw <= 70 and 14 <= bh <= 70):
                continue
            boxes.append((x1 + x, y1 + y, bw, bh))
        boxes.sort(key=lambda item: item[0])
        if len(boxes) > 3:
            boxes = boxes[-3:]
        return [self._classify_login_captcha_target(image, box) for box in boxes]

    def _detect_login_captcha_points(self, image: np.ndarray) -> dict[str, Point]:
        h, w = image.shape[:2]
        x1, y1, width, height = (
            int(w * 0.12),
            int(h * 0.42),
            int(w * 0.78),
            int(h * 0.19),
        )
        crop = image[y1 : y1 + height, x1 : x1 + width]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        mask = ((hsv[:, :, 1] > 55) & (hsv[:, :, 2] > 95)).astype("uint8") * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates: list[dict[str, float]] = []
        for contour in contours:
            x, y, bw, bh = cv2.boundingRect(contour)
            area = float(cv2.contourArea(contour))
            if area < 70 or not (10 <= bw <= 95 and 10 <= bh <= 95):
                continue
            candidate = crop[y : y + bh, x : x + bw]
            candidate_hsv = cv2.cvtColor(candidate, cv2.COLOR_BGR2HSV)
            hue = candidate_hsv[:, :, 0]
            sat = candidate_hsv[:, :, 1]
            val = candidate_hsv[:, :, 2]
            aspect = bw / float(max(1, bh))
            candidates.append(
                {
                    "x": float(x1 + x),
                    "y": float(y1 + y),
                    "width": float(bw),
                    "height": float(bh),
                    "area": area,
                    "aspect": aspect,
                    "green": float((((hue > 45) & (hue < 95) & (sat > 50) & (val > 80))).mean()),
                    "purple": float((((hue > 120) & (hue < 170) & (sat > 50) & (val > 80))).mean()),
                    "yellow": float((((hue > 15) & (hue < 42) & (sat > 50) & (val > 100))).mean()),
                    "blue": float((((hue > 90) & (hue < 132) & (sat > 50) & (val > 80))).mean()),
                }
            )

        points: dict[str, Point] = {}
        skull_candidates = [
            item
            for item in candidates
            if item["green"] >= 0.25 and 0.55 <= item["aspect"] <= 1.55
        ]
        if skull_candidates:
            item = max(skull_candidates, key=lambda value: value["green"] * value["area"])
            points["skull"] = Point(int(item["x"] + item["width"] / 2), int(item["y"] + item["height"] / 2))

        purple_candidates = [
            item
            for item in candidates
            if item["purple"] >= 0.15
            and 0.60 <= item["aspect"] <= 1.50
            and item["width"] >= 18
            and item["height"] >= 18
        ]
        if purple_candidates:
            item = max(
                purple_candidates,
                key=lambda value: value["purple"] * value["area"] - abs(value["aspect"] - 1.0) * 80.0,
            )
            points["purple_flower"] = Point(
                int(item["x"] + item["width"] / 2),
                int(item["y"] + item["height"] / 2),
            )

        circle_candidates = [
            item
            for item in candidates
            if item["yellow"] >= 0.12 and item["blue"] >= 0.04 and 0.55 <= item["aspect"] <= 1.55
        ]
        if circle_candidates:
            item = max(
                circle_candidates,
                key=lambda value: value["blue"] * 3.0 + value["yellow"] * 0.8 - abs(value["aspect"] - 1.0),
            )
            points["segmented_circle"] = Point(
                int(item["x"] + item["width"] / 2),
                int(item["y"] + item["height"] / 2),
            )

        self._record(
            {
                "type": "vision_feature",
                "feature": "account_login_captcha_candidates",
                "candidate_count": len(candidates),
                "resolved": ",".join(sorted(points.keys())),
            }
        )
        return points

    def solve_account_login_captcha_if_present(self, *, timeout_seconds: float = 3.0) -> bool:
        self._record({"type": "state", "state": "solve_account_login_captcha_if_present"})
        end_at = time() + max(0.1, timeout_seconds)
        while time() < end_at:
            image = self.bot.screenshot_image()
            order = self._detect_login_captcha_order(image)
            if len(order) != 3:
                self._sleep_with_watchdog(0.25, source="account_login_captcha_scan")
                continue

            points = self._detect_login_captcha_points(image)
            missing = [target for target in order if target not in points]
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_login_captcha",
                    "present": True,
                    "order": ",".join(order),
                    "missing": ",".join(missing),
                }
            )
            if missing:
                self.screenshot("account_login_captcha_unresolved")
                return False

            self._save_image_snapshot("before_solve_account_login_captcha", image)
            target_labels = {
                "skull": "骷髅",
                "purple_flower": "紫色圆花",
                "segmented_circle": "虚线圆",
            }
            for index, target in enumerate(order, start=1):
                self.tap(
                    f"账号登录验证码-点击{index}-{target_labels.get(target, target)}",
                    points[target],
                    wait_seconds=0.35,
                )
            h, w = image.shape[:2]
            self.tap("账号登录验证码-提交登录", Point(int(w * 0.50), int(h * 0.67)), wait_seconds=3.0)
            self.screenshot("after_solve_account_login_captcha")
            return True

        self._record(
            {
                "type": "vision_feature",
                "feature": "account_login_captcha",
                "present": False,
            }
        )
        return False

    def click_recent_login_account_if_present(self, *, timeout_seconds: float = 1.0) -> bool:
        self._record({"type": "state", "state": "click_recent_login_account_if_present"})
        end_at = time() + max(0.1, timeout_seconds)
        while time() < end_at:
            image = self.bot.screenshot_image()
            if self._recover_external_foreground_if_needed(
                source="click_recent_login_account_if_present",
                image=image,
            ):
                continue
            if self.detect_recent_login_account_chooser(image):
                h, w = image.shape[:2]
                login_region = (int(w * 0.08), int(h * 0.50), int(w * 0.84), int(h * 0.23))
                login = self.wait_for_template(
                    "切换账号流程-最近登录账号弹窗登入按钮",
                    "account_login_button",
                    timeout_seconds=0.35,
                    threshold=0.76,
                    region=login_region,
                )
                if login:
                    point = Point(*login.center)
                    self._record(
                        {
                            "type": "vision_feature",
                            "feature": "account_recent_login_submit_button",
                            "source": "template",
                            "x": login.x,
                            "y": login.y,
                            "width": login.width,
                            "height": login.height,
                            "score": round(login.score, 4),
                            "tap_x": point.x,
                            "tap_y": point.y,
                        }
                    )
                    self.tap("切换账号流程-最近登录账号弹窗点击登入", point, wait_seconds=2.0)
                    self.solve_account_login_captcha_if_present(timeout_seconds=3.0)
                    self.click_login_secondary_confirm_if_present(timeout_seconds=1.0)
                    self.screenshot("after_click_recent_login_account")
                    return True

                login = self.detect_recent_login_submit_button(image)
                if login:
                    point = Point(*login.center)
                    self.tap("切换账号流程-最近登录账号弹窗点击蓝色登入", point, wait_seconds=2.0)
                    self.solve_account_login_captcha_if_present(timeout_seconds=3.0)
                    self.click_login_secondary_confirm_if_present(timeout_seconds=1.0)
                    self.screenshot("after_click_recent_login_account")
                    return True

                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_recent_login_submit_button_missing",
                        "source": "no_list_selection_fallback",
                        "reason": "bottom_login_button_not_detected",
                    }
                )
                self.screenshot("account_recent_login_submit_button_missing")
                fallback = Point(int(w * 0.50), int(h * 0.66))
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_recent_login_submit_button",
                        "source": "bottom_coordinate_fallback",
                        "tap_x": fallback.x,
                        "tap_y": fallback.y,
                    }
                )
                self.tap("切换账号流程-最近登录账号弹窗点击底部登入兜底", fallback, wait_seconds=2.0)
                self.solve_account_login_captcha_if_present(timeout_seconds=3.0)
                self.click_login_secondary_confirm_if_present(timeout_seconds=1.0)
                self.screenshot("after_click_recent_login_account_fallback")
                return True
            self._sleep_with_watchdog(0.2, source="click_recent_login_account_if_present")
        return False

    def click_account_login_modal_if_present(self, *, timeout_seconds: float = 1.0) -> bool:
        if self.click_recent_login_account_if_present(timeout_seconds=min(0.3, timeout_seconds)):
            self._sleep_with_watchdog(0.4, source="account_login_after_recent_account")
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button_region = (int(w * 0.08), int(h * 0.50), int(w * 0.84), int(h * 0.23))
        modal = self.wait_for_template(
            "切换账号流程-灵犀账号登录弹窗",
            "account_login_modal_logo",
            timeout_seconds=timeout_seconds,
            threshold=0.74,
            region=(int(w * 0.24), int(h * 0.28), int(w * 0.52), int(h * 0.22)),
        )
        login = None
        source = "logo_template"
        if not modal:
            login = self.wait_for_template(
                "切换账号流程-登录按钮-弹窗检测",
                "account_login_button",
                timeout_seconds=min(0.8, max(0.2, timeout_seconds)),
                threshold=0.76,
                region=button_region,
            )
            source = "button_template"
        if not modal and not login:
            return False

        self._record(
            {
                "type": "vision_feature",
                "feature": "account_login_modal",
                "source": source,
                "x": modal.x if modal else login.x,
                "y": modal.y if modal else login.y,
                "width": modal.width if modal else login.width,
                "height": modal.height if modal else login.height,
                "score": round(modal.score if modal else login.score, 4),
            }
        )
        if not login:
            login = self.wait_for_template(
                "切换账号流程-登录按钮",
                "account_login_button",
                timeout_seconds=1.2,
                threshold=0.76,
                region=button_region,
            )
        if not login:
            self.screenshot("account_login_button_not_found")
            raise RuntimeError("Account switch flow found the login modal, but could not find the Login button.")

        point = Point(*login.center)
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_login_button",
                "source": "template",
                "x": login.x,
                "y": login.y,
                "width": login.width,
                "height": login.height,
                "score": round(login.score, 4),
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("切换账号流程-点击登录", point, wait_seconds=2.0)
        self.click_login_secondary_confirm_if_present(timeout_seconds=1.0)
        selected_recent_account = self.click_recent_login_account_if_present(timeout_seconds=2.0)
        if selected_recent_account:
            login_after_choice = self.wait_for_template(
                "切换账号流程-账号选择后登录按钮",
                "account_login_button",
                timeout_seconds=2.0,
                threshold=0.76,
                region=button_region,
            )
            if login_after_choice:
                self.tap(
                    "切换账号流程-账号选择后点击登录",
                    Point(*login_after_choice.center),
                    wait_seconds=2.0,
                )
                self.click_login_secondary_confirm_if_present(timeout_seconds=4.0)
        else:
            self._sleep_with_watchdog(3.0, source="account_login_wait_after_login")
            self.click_login_secondary_confirm_if_present(timeout_seconds=1.0)
        return True

    def detect_account_login_surface(self, *, timeout_seconds: float = 0.5) -> bool:
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        modal = self.wait_for_template(
            "账号批量-灵犀登录弹窗",
            "account_login_modal_logo",
            timeout_seconds=timeout_seconds,
            threshold=0.74,
            region=(int(w * 0.24), int(h * 0.28), int(w * 0.52), int(h * 0.22)),
        )
        login = None
        if not modal:
            login = self.wait_for_template(
                "账号批量-登录按钮",
                "account_login_button",
                timeout_seconds=min(0.6, max(0.2, timeout_seconds)),
                threshold=0.74,
                region=(int(w * 0.08), int(h * 0.50), int(w * 0.84), int(h * 0.18)),
            )
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_login_surface",
                "present": modal is not None or login is not None,
                "source": "logo_template" if modal else "button_template" if login else None,
                "x": modal.x if modal else login.x if login else None,
                "y": modal.y if modal else login.y if login else None,
                "width": modal.width if modal else login.width if login else None,
                "height": modal.height if modal else login.height if login else None,
                "score": round(modal.score if modal else login.score, 4) if (modal or login) else 0.0,
            }
        )
        return modal is not None or login is not None

    def detect_account_transition_loading_screen(
        self,
        image: np.ndarray | None = None,
        *,
        source: str,
        record: bool = True,
    ) -> bool:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            if record:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_transition_loading_screen",
                        "present": False,
                        "source": source,
                        "reason": "landscape_screen",
                    }
                )
            return False

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        modal_region = (int(w * 0.05), int(h * 0.30), int(w * 0.90), int(h * 0.42))
        title_region = (int(w * 0.20), int(h * 0.68), int(w * 0.60), int(h * 0.18))
        top_left_region = (0, 0, int(w * 0.20), int(h * 0.14))
        mx, my, mw, mh = self._clip_region(image, modal_region)
        tx, ty, tw, th = self._clip_region(image, title_region)
        lx, ly, lw, lh = self._clip_region(image, top_left_region)

        full_dark_ratio = float((gray < 70).mean())
        full_bright_ratio = float((gray > 220).mean())
        full_edge_ratio = float((cv2.Canny(gray, 60, 140) > 0).mean())
        modal_bright_ratio = float((gray[my : my + mh, mx : mx + mw] > 220).mean())
        title_bright_ratio = float((gray[ty : ty + th, tx : tx + tw] > 220).mean())
        top_left_bright_ratio = float((gray[ly : ly + lh, lx : lx + lw] > 220).mean())

        present = (
            modal_bright_ratio < 0.18
            and full_dark_ratio > 0.25
            and full_bright_ratio < 0.10
            and full_edge_ratio > 0.03
            and top_left_bright_ratio < 0.08
        )
        if record:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_transition_loading_screen",
                    "present": present,
                    "source": source,
                    "full_dark_ratio": round(full_dark_ratio, 4),
                    "full_bright_ratio": round(full_bright_ratio, 4),
                    "full_edge_ratio": round(full_edge_ratio, 4),
                    "modal_bright_ratio": round(modal_bright_ratio, 4),
                    "title_bright_ratio": round(title_bright_ratio, 4),
                    "top_left_bright_ratio": round(top_left_bright_ratio, 4),
                }
            )
        return present

    def close_customer_service_page_if_present(self, image: np.ndarray | None = None) -> bool:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            return False

        panel = self._crop(image, (int(w * 0.03), int(h * 0.015), int(w * 0.87), int(h * 0.30)))
        close_region = self._crop(image, (int(w * 0.90), 0, int(w * 0.10), int(h * 0.07)))
        input_region = self._crop(image, (int(w * 0.03), int(h * 0.91), int(w * 0.86), int(h * 0.08)))
        panel_hsv = cv2.cvtColor(panel, cv2.COLOR_BGR2HSV)
        close_gray = cv2.cvtColor(close_region, cv2.COLOR_BGR2GRAY)
        input_hsv = cv2.cvtColor(input_region, cv2.COLOR_BGR2HSV)
        panel_pale_ratio = float(((panel_hsv[:, :, 1] < 70) & (panel_hsv[:, :, 2] > 150)).mean())
        close_dark_ratio = float((close_gray < 90).mean())
        close_edge_ratio = float((cv2.Canny(close_gray, 60, 140) > 0).mean())
        input_pale_ratio = float(((input_hsv[:, :, 1] < 70) & (input_hsv[:, :, 2] > 150)).mean())
        present = (
            panel_pale_ratio >= 0.65
            and close_dark_ratio >= 0.08
            and close_edge_ratio >= 0.06
            and input_pale_ratio >= 0.45
        )
        point = Point(int(w * 0.945), int(h * 0.032))
        self._record(
            {
                "type": "vision_feature",
                "feature": "customer_service_page",
                "present": present,
                "panel_pale_ratio": round(panel_pale_ratio, 4),
                "close_dark_ratio": round(close_dark_ratio, 4),
                "close_edge_ratio": round(close_edge_ratio, 4),
                "input_pale_ratio": round(input_pale_ratio, 4),
                "tap_x": point.x if present else None,
                "tap_y": point.y if present else None,
            }
        )
        if not present:
            return False

        self._save_image_snapshot("before_close_customer_service_page", image)
        self.tap("账号切换-关闭客服页面", point, wait_seconds=self._fast_wait(1.2, 0.75))
        self.screenshot("after_close_customer_service_page")
        self._watchdog_reset()
        return True

    def wait_for_account_login_surface_after_transition(
        self,
        *,
        timeout_seconds: float,
        source: str,
    ) -> bool:
        end_at = time() + max(0.5, timeout_seconds)
        last_snapshot_at = 0.0
        while time() < end_at:
            if self.confirm_account_logout_if_present(timeout_seconds=0.25):
                continue
            if self.detect_account_login_surface(timeout_seconds=0.7):
                return True

            image = self.bot.screenshot_image()
            h, w = image.shape[:2]
            if self.close_customer_service_page_if_present(image):
                continue
            if self.close_server_selector_for_account_switch_if_open(
                image,
                source=f"{source}_wait_login_surface",
            ):
                continue
            if self.tap_title_return_login_for_account_switch(
                image,
                source=f"{source}_wait_login_surface",
            ):
                self.confirm_account_logout_if_present(timeout_seconds=1.0)
                continue
            if self.tap_title_logout_for_account_switch(
                image,
                source=f"{source}_wait_login_surface",
            ):
                self.confirm_account_logout_if_present(timeout_seconds=1.5)
                continue

            title_enter = self._find_template_in_image(
                image,
                "title_enter_button",
                threshold=0.68,
                region=(int(w * 0.18), int(h * 0.72), int(w * 0.66), int(h * 0.16)),
            )
            if title_enter:
                self.tap(
                    f"{source}-标题页点击前往征战唤起登录",
                    Point(*title_enter.center),
                    wait_seconds=2.0,
                )
                continue

            loading_screen = self.detect_account_transition_loading_screen(
                image,
                source=source,
                record=False,
            )
            if loading_screen:
                self._watchdog_reset()

            now = time()
            if now - last_snapshot_at >= 6.0:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_login_surface_wait",
                        "source": source,
                        "loading_screen": loading_screen,
                        "remaining_seconds": round(max(0.0, end_at - now), 1),
                    }
                )
                self._save_image_snapshot(f"{source}_waiting_login_surface", image)
                last_snapshot_at = now

            self._sleep_with_watchdog(0.5, source=f"wait_account_login_surface:{source}")

        return False

    def tap_title_logout_for_account_switch(
        self,
        image: np.ndarray | None = None,
        *,
        source: str,
    ) -> bool:
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_title_logout_button",
                "present": False,
                "source": source,
                "rejected_reason": "fixed_point_is_customer_service",
            }
        )
        return False

    def tap_title_return_login_for_account_switch(
        self,
        image: np.ndarray | None = None,
        *,
        source: str,
    ) -> bool:
        if image is None:
            image = self.bot.screenshot_image()
        marker_key, marker = self._detect_account_role_select_entry_marker(
            image,
            source=f"{source}_return_login_title_probe",
        )
        if marker_key not in {"title_select_server", "title_enter_button"} or marker is None:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_title_return_login_button",
                    "present": False,
                    "source": source,
                    "marker": marker_key,
                    "rejected_reason": "title_screen_marker_missing",
                }
            )
            return False
        h, w = image.shape[:2]
        button = self._find_template_in_image(
            image,
            "title_return_login_button",
            threshold=0.68,
            region=(0, int(h * 0.02), int(w * 0.24), int(h * 0.14)),
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_title_return_login_button",
                "present": button is not None,
                "source": source,
                "x": button.x if button else None,
                "y": button.y if button else None,
                "width": button.width if button else None,
                "height": button.height if button else None,
                "score": round(button.score, 4) if button else 0.0,
            }
        )
        if not button:
            return False

        point = Point(*button.center)
        self._watchdog_reset()
        self.tap("账号批量-标题页点击返回登录", point, wait_seconds=2.0)
        self.screenshot("after_tap_title_return_login")
        return True

    def open_account_login_modal_for_switch(
        self,
        *,
        process_current_role_before_switch: bool = False,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
    ) -> Path:
        self._record(
            {
                "type": "state",
                "state": "open_account_login_modal_for_switch",
                "process_current_role_before_switch": process_current_role_before_switch,
                "include_gacha": include_gacha,
                "include_gamecircle_signin": include_gamecircle_signin,
            }
        )
        self.screenshot("before_open_account_login_modal_for_switch")

        if self.detect_account_login_surface(timeout_seconds=0.5):
            return self.screenshot("account_login_modal_already_open")

        self.close_exit_confirm_if_present(timeout_seconds=0.2)
        if self.close_known_retreat_if_present(timeout_seconds=self._fast_timeout(0.8, 0.25)):
            self._record(
                {
                    "type": "state",
                    "state": "account_switch_cleared_known_retreat_prompt",
                }
            )
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if self.close_server_selector_for_account_switch_if_open(
            image,
            source="open_account_login_modal_for_switch",
        ):
            if self.detect_account_login_surface(timeout_seconds=0.8):
                return self.screenshot("after_close_selector_open_account_login_modal")
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]

        if self.tap_title_logout_for_account_switch(
            image,
            source="open_account_login_modal_for_switch",
        ):
            self.confirm_account_logout_if_present(timeout_seconds=1.8)
            self.close_exit_confirm_if_present(timeout_seconds=0.2)
            if self.wait_for_account_login_surface_after_transition(
                timeout_seconds=45.0,
                source="after_title_logout",
            ):
                return self.screenshot("after_title_logout_open_account_login_modal")

            image = self.bot.screenshot_image()
            h, w = image.shape[:2]

        if self.tap_title_return_login_for_account_switch(
            image,
            source="open_account_login_modal_for_switch",
        ):
            self.confirm_account_logout_if_present(timeout_seconds=1.8)
            if self.wait_for_account_login_surface_after_transition(
                timeout_seconds=60.0,
                source="after_title_return_login",
            ):
                return self.screenshot("after_title_return_login_open_account_login_modal")
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]

        title_enter = self.wait_for_template(
            "账号批量-标题页前往征战",
            "title_enter_button",
            timeout_seconds=0.35,
            threshold=0.72,
            region=(int(w * 0.22), int(h * 0.72), int(w * 0.58), int(h * 0.13)),
        )
        if title_enter:
            self.tap(
                "账号批量-标题页尝试唤起登录弹窗",
                Point(*title_enter.center),
                wait_seconds=2.0,
            )
            if self.wait_for_account_login_surface_after_transition(
                timeout_seconds=35.0,
                source="after_title_enter",
            ):
                return self.screenshot("after_title_enter_open_account_login_modal")

        self.handle_entry_preconditions(max_rounds=8, click_login_prompts=False)
        if self.detect_account_login_surface(timeout_seconds=0.6):
            return self.screenshot("after_preconditions_open_account_login_modal")
        if process_current_role_before_switch and self.detect_like_main_screen():
            self._record(
                {
                    "type": "state",
                    "state": "account_batch_bootstrap_current_role_daily_start",
                    "include_gacha": include_gacha,
                    "include_gamecircle_signin": include_gamecircle_signin,
                }
            )
            self.run_daily_signin_like_gacha(
                include_gacha=include_gacha,
                include_gamecircle_signin=include_gamecircle_signin,
            )
            self._record(
                {
                    "type": "state",
                    "state": "account_batch_bootstrap_current_role_daily_done",
                    "like_limit_reached": self._last_like_limit_reached,
                }
            )
        self._watchdog_reset()
        self.close_exit_confirm_if_present(timeout_seconds=0.2)
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        system_title = self.wait_for_template(
            "账号批量-系统设置标题",
            "account_system_settings_title",
            timeout_seconds=0.8,
            threshold=0.72,
            region=(0, 0, int(w * 0.36), int(h * 0.10)),
        )

        if not system_title:
            if not self.detect_like_main_screen():
                image = self.bot.screenshot_image()
                if self.close_server_selector_for_account_switch_if_open(
                    image,
                    source="open_account_login_modal_for_switch_retry",
                ):
                    if self.detect_account_login_surface(timeout_seconds=0.8):
                        return self.screenshot("after_close_selector_retry_open_account_login_modal")
                    image = self.bot.screenshot_image()
                if self.tap_title_logout_for_account_switch(
                    image,
                    source="open_account_login_modal_for_switch_retry",
                ):
                    self.confirm_account_logout_if_present(timeout_seconds=1.8)
                    self.close_exit_confirm_if_present(timeout_seconds=0.2)
                    if self.wait_for_account_login_surface_after_transition(
                        timeout_seconds=45.0,
                        source="after_title_logout_retry",
                    ):
                        return self.screenshot("after_title_logout_retry_open_account_login_modal")
                if self.tap_title_return_login_for_account_switch(
                    image,
                    source="open_account_login_modal_for_switch_retry",
                ):
                    self.confirm_account_logout_if_present(timeout_seconds=1.8)
                    if self.wait_for_account_login_surface_after_transition(
                        timeout_seconds=60.0,
                        source="after_title_return_login_retry",
                    ):
                        return self.screenshot("after_title_return_login_retry_open_account_login_modal")
                self.screenshot("account_batch_not_main_for_more_menu")
                raise RuntimeError("Account batch flow was not on main screen; refusing to open More/System from this state.")

            system_region = (int(w * 0.42), int(h * 0.84), int(w * 0.32), int(h * 0.14))
            more_region = (int(w * 0.64), int(h * 0.92), int(w * 0.18), int(h * 0.08))
            system_button = self.wait_for_template(
                "账号批量-更多菜单系统按钮",
                "account_system_button",
                timeout_seconds=0.8,
                threshold=0.72,
                region=system_region,
            )
            if not system_button:
                for attempt in range(3):
                    more = self.wait_for_template(
                        f"账号批量-更多按钮#{attempt + 1}",
                        "account_more_button",
                        timeout_seconds=1.2,
                        threshold=0.70,
                        region=more_region,
                    )
                    more_point = Point(*more.center) if more else Point(int(w * 0.75), int(h * 0.97))
                    self._record(
                        {
                            "type": "vision_feature",
                            "feature": "account_batch_more_button",
                            "source": "template" if more else "coordinate_fallback",
                            "attempt": attempt + 1,
                            "x": more.x if more else None,
                            "y": more.y if more else None,
                            "width": more.width if more else None,
                            "height": more.height if more else None,
                            "score": round(more.score, 4) if more else 0.0,
                            "tap_x": more_point.x,
                            "tap_y": more_point.y,
                        }
                    )
                    self.tap(f"账号批量-点击更多#{attempt + 1}", more_point, wait_seconds=1.1)
                    system_button = self.wait_for_template(
                        f"账号批量-更多菜单系统按钮#{attempt + 1}",
                        "account_system_button",
                        timeout_seconds=1.2,
                        threshold=0.72,
                        region=system_region,
                    )
                    if system_button:
                        break
                    self.screenshot(f"account_batch_system_button_retry_{attempt + 1}_not_found")

            if not system_button:
                self.screenshot("account_batch_system_button_not_found")
                raise RuntimeError("Account batch flow could not find the System button.")

            for system_attempt in range(3):
                system_point = Point(*system_button.center)
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_batch_system_button",
                        "source": "template",
                        "attempt": system_attempt + 1,
                        "x": system_button.x,
                        "y": system_button.y,
                        "width": system_button.width,
                        "height": system_button.height,
                        "score": round(system_button.score, 4),
                        "tap_x": system_point.x,
                        "tap_y": system_point.y,
                    }
                )
                self.tap(f"账号批量-点击系统#{system_attempt + 1}", system_point, wait_seconds=1.4)
                system_title = self.wait_for_template(
                    f"账号批量-系统设置标题#{system_attempt + 1}",
                    "account_system_settings_title",
                    timeout_seconds=1.5,
                    threshold=0.72,
                    region=(0, 0, int(w * 0.36), int(h * 0.10)),
                )
                if system_title:
                    break
                self.screenshot(f"account_batch_system_settings_retry_{system_attempt + 1}_not_found")
                system_button = self.wait_for_template(
                    f"账号批量-更多菜单系统按钮复查#{system_attempt + 1}",
                    "account_system_button",
                    timeout_seconds=0.8,
                    threshold=0.72,
                    region=system_region,
                ) or system_button

        if not system_title:
            self.screenshot("account_batch_system_settings_not_found")
            raise RuntimeError("Account batch flow could not confirm the System Settings page.")

        switch_button = self.wait_for_template(
            "账号批量-切换账号按钮",
            "account_switch_account_button",
            timeout_seconds=1.2,
            threshold=0.74,
            region=(int(w * 0.42), int(h * 0.76), int(w * 0.34), int(h * 0.12)),
        )
        if not switch_button:
            self.screenshot("account_batch_switch_account_button_not_found")
            raise RuntimeError("Account batch flow could not find the Switch Account button.")

        self.tap("账号批量-点击切换账号", Point(*switch_button.center), wait_seconds=2.0)
        self.confirm_account_logout_if_present(timeout_seconds=2.5)
        if self.wait_for_account_login_surface_after_transition(
            timeout_seconds=75.0,
            source="after_switch_account",
        ):
            return self.screenshot("after_open_account_login_modal_for_switch")

        self.screenshot("account_batch_login_modal_not_found")
        raise RuntimeError("Account batch flow did not reach the login modal after switching account.")

    def tap_other_account_login(self) -> Path:
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        point = Point(int(w * 0.50), int(h * 0.645))
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_other_login_link",
                "source": "coordinate",
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("账号批量-点击其他账号登录", point, wait_seconds=1.2)
        return self.screenshot("after_tap_other_account_login")

    def detect_recent_account_login_card_surface(
        self,
        image: np.ndarray | None = None,
        *,
        record: bool = True,
    ) -> bool:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        if w >= h:
            return False

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        panel_region = (int(w * 0.05), int(h * 0.30), int(w * 0.90), int(h * 0.40))
        card_region = (int(w * 0.10), int(h * 0.41), int(w * 0.80), int(h * 0.12))
        arrow_region = (int(w * 0.78), int(h * 0.43), int(w * 0.09), int(h * 0.09))
        login_region = (int(w * 0.10), int(h * 0.53), int(w * 0.80), int(h * 0.09))
        other_region = (int(w * 0.28), int(h * 0.61), int(w * 0.44), int(h * 0.07))

        px, py, pw, ph = self._clip_region(image, panel_region)
        cx, cy, cw, ch = self._clip_region(image, card_region)
        ax, ay, aw, ah = self._clip_region(image, arrow_region)
        lx, ly, lw, lh = self._clip_region(image, login_region)
        ox, oy, ow, oh = self._clip_region(image, other_region)

        panel_bright = float((gray[py : py + ph, px : px + pw] > 220).mean())
        card_bright = float((gray[cy : cy + ch, cx : cx + cw] > 220).mean())
        arrow_dark = float((gray[ay : ay + ah, ax : ax + aw] < 90).mean())

        login_crop = image[ly : ly + lh, lx : lx + lw]
        login_hsv = cv2.cvtColor(login_crop, cv2.COLOR_BGR2HSV)
        login_blue = cv2.inRange(login_hsv, np.array([95, 60, 120]), np.array([125, 255, 255]))
        login_blue_ratio = float((login_blue > 0).mean()) if login_blue.size else 0.0

        other_crop = image[oy : oy + oh, ox : ox + ow]
        other_hsv = cv2.cvtColor(other_crop, cv2.COLOR_BGR2HSV)
        other_blue = cv2.inRange(other_hsv, np.array([95, 45, 110]), np.array([130, 255, 255]))
        other_blue_ratio = float((other_blue > 0).mean()) if other_blue.size else 0.0

        present = (
            panel_bright > 0.62
            and card_bright > 0.70
            and arrow_dark > 0.006
            and login_blue_ratio > 0.22
            and other_blue_ratio > 0.018
        )
        if record:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_recent_login_card_surface",
                    "present": present,
                    "panel_bright": round(panel_bright, 4),
                    "card_bright": round(card_bright, 4),
                    "arrow_dark": round(arrow_dark, 4),
                    "login_blue_ratio": round(login_blue_ratio, 4),
                    "other_blue_ratio": round(other_blue_ratio, 4),
                }
            )
        return present

    def detect_verification_login_form(self, image: np.ndarray | None = None) -> bool:
        if image is None:
            image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (int(w * 0.62), int(h * 0.45), int(w * 0.26), int(h * 0.10))
        x, y, width, height = self._clip_region(image, region)
        crop = image[y : y + height, x : x + width]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        blue_mask = cv2.inRange(hsv, np.array([95, 60, 120]), np.array([125, 255, 255]))
        blue_ratio = float((blue_mask > 0).mean()) if blue_mask.size else 0.0
        present = blue_ratio > 0.015
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_verification_login_form",
                "present": present,
                "blue_ratio": round(blue_ratio, 4),
                "region_x": x,
                "region_y": y,
                "region_width": width,
                "region_height": height,
            }
        )
        return present

    def detect_account_input_login_form(self, image: np.ndarray | None = None) -> bool:
        if image is None:
            image = self.bot.screenshot_image()
        if self.detect_recent_account_login_card_surface(image, record=False):
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_input_login_form",
                    "present": False,
                    "reason": "recent_login_card_surface_requires_other_account_login",
                }
            )
            return False

        h, w = image.shape[:2]
        first_region = (int(w * 0.12), int(h * 0.385), int(w * 0.76), int(h * 0.07))
        second_region = (int(w * 0.12), int(h * 0.465), int(w * 0.76), int(h * 0.07))
        checkbox_region = (int(w * 0.10), int(h * 0.655), int(w * 0.07), int(h * 0.055))

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        x1, y1, w1, h1 = self._clip_region(image, first_region)
        x2, y2, w2, h2 = self._clip_region(image, second_region)
        cx, cy, cw, ch = self._clip_region(image, checkbox_region)
        first_bright = float((gray[y1 : y1 + h1, x1 : x1 + w1] > 220).mean())
        second_bright = float((gray[y2 : y2 + h2, x2 : x2 + w2] > 220).mean())
        checkbox_dark = float((gray[cy : cy + ch, cx : cx + cw] < 180).mean())
        present = first_bright > 0.55 and second_bright > 0.55 and checkbox_dark > 0.02
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_input_login_form",
                "present": present,
                "first_bright": round(first_bright, 4),
                "second_bright": round(second_bright, 4),
                "checkbox_dark": round(checkbox_dark, 4),
            }
        )
        return present

    def ensure_password_login_form(self, *, require_other_account_login: bool = False) -> Path:
        self._record(
            {
                "type": "state",
                "state": "ensure_password_login_form",
                "require_other_account_login": require_other_account_login,
            }
        )
        image = self.bot.screenshot_image()
        recent_login_card = self.detect_recent_account_login_card_surface(image)
        input_form_ready = self.detect_account_input_login_form(image)
        if recent_login_card or (require_other_account_login and not input_form_ready):
            self.tap_other_account_login()
            self._sleep_with_watchdog(0.8, source="ensure_password_login_form_after_other_account")
            image = self.bot.screenshot_image()

        if self.detect_account_input_login_form(image):
            if self.detect_verification_login_form(image):
                h, w = image.shape[:2]
                point = Point(int(w * 0.20), int(h * 0.55))
                self.tap("账号批量-切换密码登录", point, wait_seconds=1.0)
                return self.screenshot("after_switch_password_login_form")
            return self.screenshot("password_login_form_already_ready")

        for attempt in range(6):
            image = self.bot.screenshot_image()
            if self.detect_recent_account_login_card_surface(image):
                self.tap_other_account_login()
                self._sleep_with_watchdog(0.8, source=f"ensure_password_login_form_other_retry:{attempt + 1}")
                continue
            if self.detect_account_input_login_form(image):
                if self.detect_verification_login_form(image):
                    h, w = image.shape[:2]
                    point = Point(int(w * 0.20), int(h * 0.55))
                    self.tap("账号批量-切换密码登录", point, wait_seconds=1.0)
                    return self.screenshot("after_switch_password_login_form")
                return self.screenshot("password_login_form_ready_after_other_account")
            if self.detect_verification_login_form(image):
                h, w = image.shape[:2]
                point = Point(int(w * 0.20), int(h * 0.55))
                self.tap("账号批量-切换密码登录", point, wait_seconds=1.0)
                return self.screenshot("after_switch_password_login_form")
            self._sleep_with_watchdog(0.4, source=f"ensure_password_login_form:{attempt + 1}")
        return self.screenshot("password_login_form_assumed_ready")

    def clear_focused_text(self, *, max_chars: int) -> None:
        self.bot.client.keyevent("KEYCODE_MOVE_END")
        self.bot.client.keyevents(["KEYCODE_DEL"] * max_chars)

    def input_login_field(self, *, label: str, point: Point, value: str, clear_chars: int) -> None:
        self.tap(f"{label}-聚焦", point, wait_seconds=0.25)
        self.clear_focused_text(max_chars=clear_chars)
        self.bot.client.input_text(value)
        self._record(
            {
                "type": "state",
                "state": "account_login_field_entered",
                "field": label,
                "length": len(value),
            }
        )
        self._sleep_with_watchdog(0.35, source=f"input_login_field:{label}")

    def login_account_with_password(
        self,
        credential: SGZZAccountCredential,
        *,
        process_current_role_before_switch: bool = False,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
    ) -> Path:
        self._record(
            {
                "type": "state",
                "state": "login_account_with_password",
                "line_number": credential.line_number,
                "account": credential.masked_account,
                "client": credential.client,
                "package": credential.package,
                "process_current_role_before_switch": process_current_role_before_switch,
                "include_gacha": include_gacha,
                "include_gamecircle_signin": include_gamecircle_signin,
            }
        )
        self.open_account_login_modal_for_switch(
            process_current_role_before_switch=process_current_role_before_switch,
            include_gacha=include_gacha,
            include_gamecircle_signin=include_gamecircle_signin,
        )
        self.ensure_password_login_form(require_other_account_login=True)

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        phone_point = Point(int(w * 0.43), int(h * 0.417))
        password_point = Point(int(w * 0.31), int(h * 0.495))
        agree_point = Point(int(w * 0.137), int(h * 0.680))
        submit_point = Point(int(w * 0.50), int(h * 0.617))

        self.screenshot("before_account_password_login_fill")
        self.input_login_field(
            label="账号批量-手机号输入框",
            point=phone_point,
            value=credential.account,
            clear_chars=32,
        )
        self.input_login_field(
            label="账号批量-密码输入框",
            point=password_point,
            value=credential.password,
            clear_chars=64,
        )
        keyboard_image = self.bot.screenshot_image()
        if self.detect_soft_keyboard_visible(keyboard_image):
            self.bot.client.keyevent("KEYCODE_BACK")
            self._sleep_with_watchdog(0.5, source="account_password_login_hide_keyboard")
        else:
            self._record(
                {
                    "type": "state",
                    "state": "account_password_login_hide_keyboard_skipped",
                    "reason": "soft_keyboard_not_visible",
                }
            )
        self.tap("账号批量-勾选协议", agree_point, wait_seconds=0.5)
        self.tap("账号批量-提交登录", submit_point, wait_seconds=4.0)
        self.solve_account_login_captcha_if_present(timeout_seconds=3.0)
        self.screenshot("after_account_password_login_submit")
        self.click_login_secondary_confirm_if_present(timeout_seconds=6.0)

        role_marker_key, role_marker = self.wait_for_account_role_select_entry(timeout_seconds=28.0)
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_password_login_role_select_entry",
                "present": role_marker is not None,
                "template": role_marker_key,
                "x": role_marker.x if role_marker else None,
                "y": role_marker.y if role_marker else None,
                "width": role_marker.width if role_marker else None,
                "height": role_marker.height if role_marker else None,
                "score": round(role_marker.score, 4) if role_marker else 0.0,
                "account": credential.masked_account,
            }
        )
        if not role_marker:
            self.screenshot("account_password_login_role_select_not_found")
            raise RuntimeError(
                f"Account batch flow could not reach role-select entry after login: {credential.masked_account}."
            )
        return self.screenshot("after_account_password_login")

    def login_configured_account(
        self,
        credential: SGZZAccountCredential,
        *,
        process_current_role_before_switch: bool = False,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
    ) -> Path:
        if credential.client == "小米":
            self._record(
                {
                    "type": "state",
                    "state": "xiaomi_cached_login_wait_start",
                    "account": credential.masked_account,
                    "account_key": credential.account_key,
                    "client": credential.client,
                    "package": credential.package,
                }
            )
            end_at = time() + 90.0
            role_marker_key: str | None = None
            role_marker: Match | None = None
            while time() < end_at:
                role_marker_key, role_marker = self.wait_for_account_role_select_entry(timeout_seconds=6.0)
                if role_marker:
                    break
                if self.detect_like_main_screen():
                    self._record(
                        {
                            "type": "vision_feature",
                            "feature": "xiaomi_cached_login_main_screen",
                            "present": True,
                            "account": credential.masked_account,
                            "source": "main_screen_detected",
                        }
                    )
                    return self.screenshot("after_xiaomi_cached_login_main_screen")
                self.handle_entry_preconditions(max_rounds=2)

            self._record(
                {
                    "type": "vision_feature",
                    "feature": "xiaomi_cached_login_role_select_entry",
                    "present": role_marker is not None,
                    "template": role_marker_key,
                    "x": role_marker.x if role_marker else None,
                    "y": role_marker.y if role_marker else None,
                    "width": role_marker.width if role_marker else None,
                    "height": role_marker.height if role_marker else None,
                    "score": round(role_marker.score, 4) if role_marker else 0.0,
                    "account": credential.masked_account,
                }
            )
            if not role_marker:
                if self.detect_like_main_screen():
                    self._record(
                        {
                            "type": "vision_feature",
                            "feature": "xiaomi_cached_login_main_screen",
                            "present": True,
                            "account": credential.masked_account,
                            "source": "final_main_screen_detected",
                        }
                    )
                    return self.screenshot("after_xiaomi_cached_login_main_screen")
                path = self.screenshot("xiaomi_cached_login_role_select_not_found")
                raise RuntimeError(
                    f"Xiaomi cached login did not reach the role-select entry or main screen: "
                    f"{credential.masked_account}. Check the emulator login page in {path}."
                )
            return self.screenshot("after_xiaomi_cached_login")

        if credential.client != DEFAULT_SGZZ_CLIENT:
            path = self.screenshot(f"{credential.client}_client_login_flow_pending")
            self._record(
                {
                    "type": "state",
                    "state": "account_client_login_flow_pending",
                    "account": credential.masked_account,
                    "account_key": credential.account_key,
                    "client": credential.client,
                    "package": credential.package,
                    "screenshot": str(path),
                }
            )
            raise RuntimeError(
                f"{credential.client} client was launched ({credential.package}), "
                "but its login flow has not been recorded yet."
            )
        return self.login_account_with_password(
            credential,
            process_current_role_before_switch=process_current_role_before_switch,
            include_gacha=include_gacha,
            include_gamecircle_signin=include_gamecircle_signin,
        )

    @staticmethod
    def _android_node_center(node: dict[str, str]) -> Point | None:
        bounds = str(node.get("bounds") or "")
        match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
        if not match:
            return None
        left, top, right, bottom = (int(value) for value in match.groups())
        if right <= left or bottom <= top:
            return None
        return Point((left + right) // 2, (top + bottom) // 2)

    def _dump_xiaomi_login_nodes(self) -> list[dict[str, str]]:
        remote_path = "/sdcard/sgzz_xiaomi_login.xml"
        try:
            self.bot.client.shell(["uiautomator", "dump", remote_path], timeout=8.0)
            raw = self.bot.client.shell(["cat", remote_path], timeout=8.0)
            xml_start = raw.find("<?xml")
            if xml_start < 0:
                return []
            root = ET.fromstring(raw[xml_start:])
            return [dict(node.attrib) for node in root.iter("node")]
        except Exception as exc:
            self._record(
                {
                    "type": "state",
                    "state": "xiaomi_login_ui_dump_failed",
                    "error": str(exc),
                }
            )
            return []

    def _record_xiaomi_login_ui_state(self, state: str) -> None:
        if state == self._xiaomi_login_ui_state:
            return
        self._xiaomi_login_ui_state = state
        self._record(
            {
                "type": "state",
                "state": state,
                "client": "小米",
                "package": self.package,
            }
        )

    def handle_xiaomi_login_interstitial(self) -> str | None:
        try:
            focus = self.bot.client.current_focus()
        except Exception:
            return None
        if "com.xiaomi.gamecenter" not in focus:
            return None

        nodes = self._dump_xiaomi_login_nodes()
        if not nodes:
            self._record_xiaomi_login_ui_state("xiaomi_login_sdk_loading")
            self._watchdog_reset()
            return "sdk_loading"

        for node in nodes:
            text = str(node.get("text") or "").strip()
            if "同意并继续" not in text:
                continue
            point = self._android_node_center(node)
            if point is None:
                continue
            self._record_xiaomi_login_ui_state("xiaomi_login_privacy_confirmation")
            self.tap("小米登录-同意并继续", point, wait_seconds=2.0)
            self._watchdog_reset()
            return "privacy_confirmed"

        texts = [str(node.get("text") or "").strip() for node in nodes]
        verification_page = any("验证码" in text for text in texts)
        if verification_page:
            entered_length = 0
            for node in nodes:
                if node.get("class") != "android.widget.EditText":
                    continue
                value = str(node.get("text") or "").strip()
                if value.isdigit():
                    entered_length = max(entered_length, len(value))
            if entered_length == 6:
                for node in nodes:
                    if str(node.get("text") or "").strip() != "确定":
                        continue
                    point = self._android_node_center(node)
                    if point is None:
                        continue
                    self._record_xiaomi_login_ui_state("xiaomi_sms_code_ready")
                    self._record(
                        {
                            "type": "state",
                            "state": "xiaomi_sms_code_length_confirmed",
                            "length": entered_length,
                        }
                    )
                    self.tap("小米登录-验证码已满6位-确定", point, wait_seconds=3.0)
                    self._watchdog_reset()
                    return "sms_confirmed"
            self._record_xiaomi_login_ui_state("xiaomi_sms_code_waiting")
            self._watchdog_reset()
            return "sms_waiting"

        if any("登录中" in text for text in texts):
            self._record_xiaomi_login_ui_state("xiaomi_cached_login_in_progress")
            self._watchdog_reset()
            return "cached_login_in_progress"

        self._record_xiaomi_login_ui_state("xiaomi_login_sdk_visible")
        self._watchdog_reset()
        return "sdk_visible"

    def _detect_account_role_select_entry_marker(
        self,
        image: np.ndarray,
        *,
        source: str,
    ) -> tuple[str | None, Match | None]:
        h, w = image.shape[:2]
        candidates: tuple[tuple[str, float, tuple[int, int, int, int] | None], ...] = (
            ("title_select_server", 0.66, None),
            ("title_enter_button", 0.66, None),
            ("server_selector_title", 0.66, None),
            (
                "title_select_server",
                0.64,
                (int(w * 0.45), int(h * 0.66), int(w * 0.40), int(h * 0.13)),
            ),
            (
                "title_enter_button",
                0.64,
                (int(w * 0.18), int(h * 0.72), int(w * 0.66), int(h * 0.16)),
            ),
            (
                "server_selector_title",
                0.64,
                (int(w * 0.24), 0, int(w * 0.52), int(h * 0.12)),
            ),
        )
        for candidate, threshold, region in candidates:
            marker = self._find_template_in_image(
                image,
                candidate,
                threshold=threshold,
                region=region,
            )
            if not marker:
                continue
            self._record(
                {
                    "type": "match",
                    "label": "切换账号流程-切换角色入口",
                    "template": TEMPLATES[candidate],
                    "source": source,
                    "threshold": threshold,
                    "region": list(region) if region is not None else None,
                    "x": marker.x,
                    "y": marker.y,
                    "width": marker.width,
                    "height": marker.height,
                    "score": round(marker.score, 4),
                }
            )
            return candidate, marker
        return None, None

    def wait_for_account_role_select_entry(self, *, timeout_seconds: float = 12.0) -> tuple[str | None, Match | None]:
        role_marker = None
        role_marker_key = None
        end_at = time() + timeout_seconds
        while time() < end_at:
            image = self.bot.screenshot_image()
            if self.detect_exit_confirm_in_image(image):
                self._record(
                    {
                        "type": "state",
                        "state": "account_role_select_entry_blocked_by_exit_confirm",
                    }
                )
                self.close_exit_confirm_if_present(timeout_seconds=0.2)
                self._sleep_with_watchdog(0.4, source="wait_for_account_role_select_entry_exit_confirm")
                continue
            if self.client_name == "小米":
                role_marker_key, role_marker = self._detect_account_role_select_entry_marker(
                    image,
                    source="xiaomi_login_wait",
                )
                if role_marker:
                    break
                xiaomi_state = self.handle_xiaomi_login_interstitial()
                if xiaomi_state is not None:
                    sleep(0.6)
                    continue
            if self.click_recent_login_account_if_present(timeout_seconds=0.2):
                self.click_account_login_modal_if_present(timeout_seconds=1.5)
                self.click_login_secondary_confirm_if_present(timeout_seconds=1.0)
                continue
            if self.click_account_login_modal_if_present(timeout_seconds=0.2):
                self.click_login_secondary_confirm_if_present(timeout_seconds=1.0)
                continue
            if self.click_login_secondary_confirm_if_present(timeout_seconds=0.25):
                continue
            image = self.bot.screenshot_image()
            if self.detect_exit_confirm_in_image(image):
                self._record(
                    {
                        "type": "state",
                        "state": "account_role_select_entry_blocked_by_exit_confirm_after_clicks",
                    }
                )
                self.close_exit_confirm_if_present(timeout_seconds=0.2)
                continue
            if self.detect_recent_login_account_chooser(image):
                self._record(
                    {
                        "type": "state",
                        "state": "account_role_select_entry_blocked_by_recent_login_chooser",
                    }
                )
                continue
            if self.detect_title_login_in_progress(
                image,
                source="wait_for_account_role_select_entry",
            ):
                self._record(
                    {
                        "type": "state",
                        "state": "account_role_select_entry_blocked_by_title_login_in_progress",
                    }
                )
                self._sleep_with_watchdog(0.8, source="wait_for_account_role_select_entry_login_in_progress")
                continue
            role_marker_key, role_marker = self._detect_account_role_select_entry_marker(
                image,
                source="wait_loop",
            )
            if role_marker:
                break
            self._sleep_with_watchdog(0.4, source="wait_for_account_role_select_entry")
        if not role_marker:
            image = self.bot.screenshot_image()
            if not self.detect_title_login_in_progress(
                image,
                source="wait_for_account_role_select_entry_final_rescan",
            ):
                role_marker_key, role_marker = self._detect_account_role_select_entry_marker(
                    image,
                    source="final_rescan_after_timeout",
                )
        return role_marker_key, role_marker

    def switch_account_to_role_select(self) -> Path:
        self._record({"type": "state", "state": "switch_account_to_role_select"})
        self.screenshot("before_account_switch_to_role_select")

        role_marker_key, role_marker = self.wait_for_account_role_select_entry(timeout_seconds=1.2)
        if role_marker:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_role_select_entry",
                    "present": True,
                    "template": role_marker_key,
                    "x": role_marker.x,
                    "y": role_marker.y,
                    "width": role_marker.width,
                    "height": role_marker.height,
                    "score": round(role_marker.score, 4),
                    "source": "already_on_role_select_entry",
                }
            )
            return self.screenshot("after_account_switch_to_role_select")

        if self.click_account_login_modal_if_present(timeout_seconds=0.8):
            role_marker_key, role_marker = self.wait_for_account_role_select_entry(timeout_seconds=12.0)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_role_select_entry",
                    "present": role_marker is not None,
                    "template": role_marker_key,
                    "x": role_marker.x if role_marker else None,
                    "y": role_marker.y if role_marker else None,
                    "width": role_marker.width if role_marker else None,
                    "height": role_marker.height if role_marker else None,
                    "score": round(role_marker.score, 4) if role_marker else 0.0,
                }
            )
            if not role_marker:
                self.screenshot("account_role_select_entry_not_confirmed")
                self._finish_black_screen_watchdog_if_active(
                    source="account_role_select_after_login_failure"
                )
                raise RuntimeError("Account switch flow did not reach the role-select entry screen after login.")
            return self.screenshot("after_account_switch_to_role_select")

        prepared_from_intermediate = self.handle_entry_preconditions(max_rounds=8)
        self._record(
            {
                "type": "state",
                "state": "account_switch_intermediate_preconditions",
                "handled": prepared_from_intermediate,
            }
        )
        if prepared_from_intermediate:
            role_marker_key, role_marker = self.wait_for_account_role_select_entry(timeout_seconds=1.2)
            if role_marker:
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_role_select_entry",
                        "present": True,
                        "template": role_marker_key,
                        "x": role_marker.x,
                        "y": role_marker.y,
                        "width": role_marker.width,
                        "height": role_marker.height,
                        "score": round(role_marker.score, 4),
                        "source": "after_intermediate_preconditions",
                    }
                )
                return self.screenshot("after_account_switch_to_role_select")

        main_screen_ready = self.detect_like_main_screen()
        if not main_screen_ready:
            main_screen_ready = self.recover_to_main_screen(max_steps=10)
            self._record(
                {
                    "type": "state",
                    "state": "account_switch_main_screen_recovery",
                    "recovered": main_screen_ready,
                }
            )
        if not main_screen_ready:
            image = self.bot.screenshot_image()
            self._restart_game_after_stuck(
                source="account_switch_main_screen_recovery_failed",
                elapsed_seconds=0.0,
                stable_regions=["account_switch_recovery"],
                diffs={},
                image=image,
            )

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        system_title = self.wait_for_template(
            "切换账号流程-系统设置标题",
            "account_system_settings_title",
            timeout_seconds=0.8,
            threshold=0.72,
            region=(0, 0, int(w * 0.36), int(h * 0.10)),
        )

        if not system_title:
            system_region = (int(w * 0.42), int(h * 0.84), int(w * 0.32), int(h * 0.14))
            more_region = (int(w * 0.64), int(h * 0.92), int(w * 0.18), int(h * 0.08))
            system_button = self.wait_for_template(
                "切换账号流程-更多菜单系统按钮",
                "account_system_button",
                timeout_seconds=0.8,
                threshold=0.72,
                region=system_region,
            )
            if not system_button:
                for more_attempt in range(3):
                    more = self.wait_for_template(
                        f"切换账号流程-更多按钮#{more_attempt + 1}",
                        "account_more_button",
                        timeout_seconds=1.2,
                        threshold=0.70,
                        region=more_region,
                    )
                    if more:
                        more_point = Point(*more.center)
                        source = "template"
                        more_record = {
                            "x": more.x,
                            "y": more.y,
                            "width": more.width,
                            "height": more.height,
                            "score": round(more.score, 4),
                        }
                    else:
                        more_point = Point(int(w * 0.75), int(h * 0.97))
                        source = "coordinate_fallback"
                        more_record = {}

                    self._record(
                        {
                            "type": "vision_feature",
                            "feature": "account_more_button",
                            "source": source,
                            "attempt": more_attempt + 1,
                            **more_record,
                            "tap_x": more_point.x,
                            "tap_y": more_point.y,
                        }
                    )
                    self.tap(f"切换账号流程-点击更多#{more_attempt + 1}", more_point, wait_seconds=1.1)

                    system_button = self.wait_for_template(
                        f"切换账号流程-更多菜单系统按钮#{more_attempt + 1}",
                        "account_system_button",
                        timeout_seconds=1.2,
                        threshold=0.72,
                        region=system_region,
                    )
                    if system_button:
                        break
                    self.screenshot(f"account_system_button_retry_{more_attempt + 1}_not_found")

            if not system_button:
                self.screenshot("account_system_button_not_found")
                raise RuntimeError("Account switch flow could not find the System button in the More menu.")

            for system_attempt in range(3):
                system_point = Point(*system_button.center)
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_system_button",
                        "source": "template",
                        "attempt": system_attempt + 1,
                        "x": system_button.x,
                        "y": system_button.y,
                        "width": system_button.width,
                        "height": system_button.height,
                        "score": round(system_button.score, 4),
                        "tap_x": system_point.x,
                        "tap_y": system_point.y,
                    }
                )
                self.tap(f"切换账号流程-点击系统#{system_attempt + 1}", system_point, wait_seconds=1.4)

                system_title = self.wait_for_template(
                    f"切换账号流程-系统设置标题#{system_attempt + 1}",
                    "account_system_settings_title",
                    timeout_seconds=1.5,
                    threshold=0.72,
                    region=(0, 0, int(w * 0.36), int(h * 0.10)),
                )
                if system_title:
                    break
                self.screenshot(f"account_system_settings_retry_{system_attempt + 1}_not_found")
                system_button = self.wait_for_template(
                    f"切换账号流程-更多菜单系统按钮复查#{system_attempt + 1}",
                    "account_system_button",
                    timeout_seconds=0.8,
                    threshold=0.72,
                    region=system_region,
                ) or system_button

        if not system_title:
            self.screenshot("account_system_settings_not_found")
            raise RuntimeError("Account switch flow could not confirm the System Settings page.")

        self._record(
            {
                "type": "vision_feature",
                "feature": "account_system_settings_title",
                "source": "template",
                "x": system_title.x,
                "y": system_title.y,
                "width": system_title.width,
                "height": system_title.height,
                "score": round(system_title.score, 4),
            }
        )

        switch_button = self.wait_for_template(
            "切换账号流程-切换账号按钮",
            "account_switch_account_button",
            timeout_seconds=1.2,
            threshold=0.74,
            region=(int(w * 0.42), int(h * 0.76), int(w * 0.34), int(h * 0.12)),
        )
        if not switch_button:
            self.screenshot("account_switch_account_button_not_found")
            raise RuntimeError("Account switch flow could not find the Switch Account button.")

        switch_point = Point(*switch_button.center)
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_switch_account_button",
                "source": "template",
                "x": switch_button.x,
                "y": switch_button.y,
                "width": switch_button.width,
                "height": switch_button.height,
                "score": round(switch_button.score, 4),
                "tap_x": switch_point.x,
                "tap_y": switch_point.y,
            }
        )
        self.tap("切换账号流程-点击切换账号", switch_point, wait_seconds=4.0)
        self.confirm_account_logout_if_present(timeout_seconds=2.5)

        role_marker_key = None
        role_marker = None
        end_at = time() + (60.0 if self.client_name == "小米" else 24.0)
        while time() < end_at:
            if self.confirm_account_logout_if_present(timeout_seconds=0.35):
                continue
            if self.click_account_login_modal_if_present(timeout_seconds=1.0):
                role_marker_key, role_marker = self.wait_for_account_role_select_entry(timeout_seconds=12.0)
                break
            role_marker_key, role_marker = self.wait_for_account_role_select_entry(timeout_seconds=1.2)
            if role_marker:
                break

        self._record(
            {
                "type": "vision_feature",
                "feature": "account_role_select_entry",
                "present": role_marker is not None,
                "template": role_marker_key,
                "x": role_marker.x if role_marker else None,
                "y": role_marker.y if role_marker else None,
                "width": role_marker.width if role_marker else None,
                "height": role_marker.height if role_marker else None,
                "score": round(role_marker.score, 4) if role_marker else 0.0,
            }
        )
        if not role_marker:
            self.screenshot("account_role_select_entry_not_confirmed")
            self._finish_black_screen_watchdog_if_active(
                source="account_role_select_final_failure"
            )
            raise RuntimeError("Account switch flow did not reach the role-select entry screen.")

        return self.screenshot("after_account_switch_to_role_select")

    def login_current_account_and_select_last_role(self) -> Path:
        self._record({"type": "state", "state": "login_current_account_and_select_last_role"})
        self.screenshot("before_account_login_and_select_last_role")

        logged_in = self.click_account_login_modal_if_present(timeout_seconds=0.8)
        self._record(
            {
                "type": "vision_feature",
                "feature": "account_optional_login_before_role_select",
                "clicked": logged_in,
            }
        )
        if logged_in:
            role_marker_key, role_marker = self.wait_for_account_role_select_entry(timeout_seconds=12.0)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "account_role_select_entry",
                    "present": role_marker is not None,
                    "template": role_marker_key,
                    "x": role_marker.x if role_marker else None,
                    "y": role_marker.y if role_marker else None,
                    "width": role_marker.width if role_marker else None,
                    "height": role_marker.height if role_marker else None,
                    "score": round(role_marker.score, 4) if role_marker else 0.0,
                }
            )
            if not role_marker:
                self.screenshot("account_role_select_entry_not_confirmed_after_login")
                self._finish_black_screen_watchdog_if_active(
                    source="account_login_select_last_role_after_login_failure"
                )
                raise RuntimeError("Account role switch flow did not reach the title/server-select entry after login.")

        selected_path = self.select_last_entry_in_server_selector(confirm_and_enter=True)
        self._record(
            {
                "type": "state",
                "state": "account_login_and_select_last_role_done",
                "selected_path": str(selected_path),
            }
        )
        return self.screenshot("after_account_login_and_select_last_role")

    def close_known_retreat_if_present(self, *, timeout_seconds: float = 1.0) -> bool:
        self._record({"type": "state", "state": "close_known_retreat_if_present"})
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (int(w * 0.20), int(h * 0.42), int(w * 0.45), int(h * 0.18))
        button = self._find_template_in_image(
            image,
            "main_known_retreat_button",
            threshold=0.78,
            region=region,
        )
        if not button and timeout_seconds > 0.4:
            button = self.wait_for_template(
                "异常处理-已知退下按钮",
                "main_known_retreat_button",
                timeout_seconds=timeout_seconds,
                threshold=0.78,
                region=region,
            )
        self._record(
            {
                "type": "vision_feature",
                "feature": "main_known_retreat_button",
                "present": button is not None,
                "x": button.x if button else None,
                "y": button.y if button else None,
                "width": button.width if button else None,
                "height": button.height if button else None,
                "score": round(button.score, 4) if button else 0.0,
            }
        )
        if not button:
            return False

        for attempt in range(1, 4):
            point = Point(button.x + button.width // 2, button.y + int(button.height * 0.62))
            self.tap(f"异常处理-点击已知退下({attempt})", point, wait_seconds=0.8)
            still_present = self.wait_for_template(
                f"异常处理-已知退下按钮复查({attempt})",
                "main_known_retreat_button",
                timeout_seconds=0.6,
                threshold=0.78,
                region=region,
            )
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "main_known_retreat_button_after_tap",
                    "attempt": attempt,
                    "present": still_present is not None,
                    "x": still_present.x if still_present else None,
                    "y": still_present.y if still_present else None,
                    "width": still_present.width if still_present else None,
                    "height": still_present.height if still_present else None,
                    "score": round(still_present.score, 4) if still_present else 0.0,
                }
            )
            if not still_present:
                self.screenshot("after_close_known_retreat")
                return True
            button = still_present

        self.screenshot("known_retreat_still_present_after_click")
        raise RuntimeError("Known retreat prompt remained after clicking 已知退下.")

    def complete_known_retreat_prompt(self) -> Path:
        closed = self.close_known_retreat_if_present(timeout_seconds=1.5)
        self._record(
            {
                "type": "state",
                "state": "known_retreat_prompt_done",
                "closed": closed,
            }
        )
        return self.screenshot("after_known_retreat_prompt")

    def complete_tongpao_feature_prompt_if_present(self, *, timeout_seconds: float = 1.0) -> bool:
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (int(w * 0.25), int(h * 0.78), int(w * 0.60), int(h * 0.14))
        marker = self._find_template_in_image(
            image,
            "tongpao_feature_marker",
            threshold=0.72,
            region=region,
        )
        if not marker and timeout_seconds > 0.4:
            marker = self.wait_for_template(
                "同袍功能引导标识-可选检测",
                "tongpao_feature_marker",
                timeout_seconds=timeout_seconds,
                threshold=0.72,
                region=region,
            )
        self._record(
            {
                "type": "vision_feature",
                "feature": "optional_tongpao_feature_marker",
                "present": marker is not None,
                "x": marker.x if marker else None,
                "y": marker.y if marker else None,
                "width": marker.width if marker else None,
                "height": marker.height if marker else None,
                "score": round(marker.score, 4) if marker else 0.0,
            }
        )
        if not marker:
            return False

        self.complete_tongpao_feature_prompt()
        self.back_to_main_from_alliance()
        return True

    def run_daily_signin_like_gacha(
        self,
        *,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
    ) -> Path:
        self._record(
            {
                "type": "state",
                "state": "run_daily_signin_like_gacha",
                "include_gacha": include_gacha,
                "include_gamecircle_signin": include_gamecircle_signin,
            }
        )
        self.screenshot("before_daily_signin_like_gacha")

        self.handle_entry_preconditions(max_rounds=int(self._fast_timeout(8, 4)))
        signin_closed = self.close_signin_reward_if_present(
            timeout_seconds=self._fast_timeout(1.5, 0.35)
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "daily_signin_reward",
                "closed": signin_closed,
            }
        )
        known_retreat_closed = self.close_known_retreat_if_present(
            timeout_seconds=self._fast_timeout(1.0, 0.25)
        )
        tongpao_handled = self.complete_tongpao_feature_prompt_if_present(
            timeout_seconds=self._fast_timeout(1.0, 0.30)
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "daily_tongpao_prompt",
                "handled": tongpao_handled,
            }
        )
        if signin_closed or known_retreat_closed or tongpao_handled:
            self.close_signin_reward_if_present(timeout_seconds=self._fast_timeout(0.8, 0.25))
            self.close_known_retreat_if_present(timeout_seconds=self._fast_timeout(1.0, 0.25))
        self.close_military_council_if_present(timeout_seconds=self._fast_timeout(1.0, 0.30))
        self.close_exit_confirm_if_present(timeout_seconds=self._fast_timeout(0.8, 0.25))

        if not self.detect_like_main_screen():
            recovered = self.recover_to_main_screen(max_steps=6)
            self._record(
                {
                    "type": "state",
                    "state": "daily_recover_before_like",
                    "recovered": recovered,
                }
            )
            if not recovered:
                self.screenshot("daily_main_screen_not_ready_before_like")
                raise RuntimeError("Daily flow expected main screen before like flow.")

        like_done = True
        self._last_like_limit_reached = False
        self._last_daily_like_done = False
        self.open_friends_list_for_like()
        try:
            self.click_dabai_friend_button_for_like()
            self.click_personal_info_button_for_like()
            self.click_personal_home_view_button_for_like()
            self.click_home_like_button_for_like(clicks=5)
            self.click_home_back_button_for_like()
            self.click_friends_back_button_for_like()
            self.close_exit_confirm_if_present(timeout_seconds=self._fast_timeout(0.5, 0.20))
        except RuntimeError as exc:
            if "friend card" not in str(exc):
                raise
            like_done = False
            self._record(
                {
                    "type": "state",
                    "state": "daily_like_target_missing_skip",
                    "error": str(exc),
                }
            )
            self.screenshot("daily_like_target_missing_skip")
            try:
                request_sent = self.request_missing_like_friend()
                self._record(
                    {
                        "type": "state",
                        "state": "daily_like_missing_friend_request_done",
                        "request_sent_or_pending": request_sent,
                    }
                )
            except Exception as add_exc:  # noqa: BLE001
                self._record(
                    {
                        "type": "state",
                        "state": "daily_like_missing_friend_request_failed",
                        "error": str(add_exc),
                    }
                )
                self.screenshot("daily_like_missing_friend_request_failed")
            self.close_friend_query_add_modal_if_present(timeout_seconds=0.8)
            retried_like_after_request = False
            if request_sent:
                try:
                    try:
                        self.click_friends_back_button_for_like()
                    except RuntimeError as back_exc:
                        self._record(
                            {
                                "type": "state",
                                "state": "daily_like_target_missing_back_retry_before_reopen",
                                "error": str(back_exc),
                            }
                        )
                        self.click_any_visible_back_if_present(timeout_seconds=0.6)
                    if not self.detect_like_main_screen():
                        self.recover_to_main_screen(max_steps=6)
                    self.open_friends_list_for_like()
                    self.click_dabai_friend_button_for_like()
                    self.click_personal_info_button_for_like()
                    self.click_personal_home_view_button_for_like()
                    self.click_home_like_button_for_like(clicks=5)
                    self.click_home_back_button_for_like()
                    self.click_friends_back_button_for_like()
                    self.close_exit_confirm_if_present(timeout_seconds=self._fast_timeout(0.5, 0.20))
                    like_done = True
                    retried_like_after_request = True
                    self._record(
                        {
                            "type": "state",
                            "state": "daily_like_missing_friend_retry_done",
                        }
                    )
                except RuntimeError as retry_exc:
                    self._record(
                        {
                            "type": "state",
                            "state": "daily_like_missing_friend_retry_failed",
                            "error": str(retry_exc),
                        }
                    )
                    self.screenshot("daily_like_missing_friend_retry_failed")
            if not retried_like_after_request:
                try:
                    self.click_friends_back_button_for_like()
                except RuntimeError as back_exc:
                    self._record(
                        {
                            "type": "state",
                            "state": "daily_like_target_missing_back_retry",
                            "error": str(back_exc),
                        }
                    )
                    self.click_any_visible_back_if_present(timeout_seconds=0.6)
                if not self.detect_like_main_screen():
                    self.recover_to_main_screen(max_steps=6)
        self._record(
            {
                "type": "vision_feature",
                "feature": "daily_like",
                "done": like_done,
                "limit_reached": self._last_like_limit_reached,
            }
        )
        self._last_daily_like_done = like_done

        if not self.detect_like_main_screen():
            recovered = self.recover_to_main_screen(max_steps=6)
            self._record(
                {
                    "type": "state",
                    "state": "daily_recover_before_gacha",
                    "recovered": recovered,
                }
            )
            if not recovered:
                self.screenshot("daily_main_screen_not_ready_before_gacha")
                raise RuntimeError("Daily flow expected main screen before gacha flow.")

        if not include_gacha:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "daily_free_gacha",
                    "done": False,
                    "skipped": True,
                }
            )
        else:
            gacha_done = self.run_free_gacha_if_available()
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "daily_free_gacha",
                    "done": gacha_done,
                }
            )

        if include_gamecircle_signin:
            if not self.detect_like_main_screen():
                recovered = self.recover_to_main_screen(max_steps=6)
                self._record(
                    {
                        "type": "state",
                        "state": "daily_recover_before_gamecircle_signin",
                        "recovered": recovered,
                    }
                )
                if not recovered:
                    self.screenshot("daily_main_screen_not_ready_before_gamecircle_signin")
                    raise RuntimeError("Daily flow expected main screen before game circle sign-in.")
            self.run_gamecircle_signin()
        else:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "gamecircle_signin",
                    "done": False,
                    "skipped": True,
                }
            )

        return self.screenshot("after_daily_signin_like_gacha")

    def run_account_role_daily_cycle(
        self,
        *,
        max_cycles: int = 3,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
    ) -> Path:
        if max_cycles < 1:
            raise ValueError("Account role daily cycle count must be at least 1.")

        self._record(
            {
                "type": "state",
                "state": "run_account_role_daily_cycle",
                "max_cycles": max_cycles,
                "include_gacha": include_gacha,
                "include_gamecircle_signin": include_gamecircle_signin,
            }
        )
        self.screenshot("before_account_role_daily_cycle")

        for index in range(max_cycles):
            cycle = index + 1
            self._record(
                {
                    "type": "state",
                    "state": "account_role_daily_cycle_iteration",
                    "iteration": cycle,
                    "max_cycles": max_cycles,
                }
            )
            self.switch_account_to_role_select()
            self.login_current_account_and_select_last_role()
            self.run_daily_signin_like_gacha(
                include_gacha=include_gacha,
                include_gamecircle_signin=include_gamecircle_signin,
            )

        self._record(
            {
                "type": "state",
                "state": "account_role_daily_cycle_done",
                "max_cycles": max_cycles,
            }
        )
        return self.screenshot("after_account_role_daily_cycle")

    def run_account_remaining_roles_daily_cycle(
        self,
        *,
        max_cycles: int = 20,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
    ) -> Path:
        if max_cycles < 1:
            raise ValueError("Account remaining-role cycle count must be at least 1.")

        role_selection_order = os.environ.get("SGZZ_ROLE_SELECTION_ORDER", "bottom").strip().lower()
        if role_selection_order not in {"top", "bottom"}:
            role_selection_order = "bottom"
        row_repeat_threshold = 0.88
        title_repeat_threshold = 0.96
        ingame_repeat_threshold = 0.94
        like_limit_stop_threshold = max(
            1,
            int(os.environ.get("SGZZ_LIKE_LIMIT_CONSECUTIVE_STOP_COUNT", "3")),
        )
        incomplete_role_retry_limit = max(
            0,
            min(120, int(os.environ.get("SGZZ_INCOMPLETE_ROLE_RETRY_LIMIT", "20"))),
        )
        incomplete_role_retry_wait_seconds = max(
            0.0,
            min(25.0, float(os.environ.get("SGZZ_INCOMPLETE_ROLE_RETRY_WAIT_SECONDS", "15"))),
        )
        entry_failure_title_match_threshold = max(
            0.70,
            min(
                0.98,
                float(os.environ.get("SGZZ_ROLE_ENTRY_FAILURE_TITLE_MATCH_THRESHOLD", "0.86")),
            ),
        )
        self._record(
            {
                "type": "state",
                "state": "run_account_remaining_roles_daily_cycle",
                "max_cycles": max_cycles,
                "include_gacha": include_gacha,
                "include_gamecircle_signin": include_gamecircle_signin,
                "role_selection_order": role_selection_order,
                "row_repeat_threshold": row_repeat_threshold,
                "title_repeat_threshold": title_repeat_threshold,
                "ingame_repeat_threshold": ingame_repeat_threshold,
                "like_limit_stop_threshold": like_limit_stop_threshold,
                "incomplete_role_retry_limit": incomplete_role_retry_limit,
                "incomplete_role_retry_wait_seconds": incomplete_role_retry_wait_seconds,
                "entry_failure_title_match_threshold": entry_failure_title_match_threshold,
            }
        )
        self.screenshot("before_account_remaining_roles_daily_cycle")

        first_row_template: np.ndarray | None = None
        first_title_template: np.ndarray | None = None
        first_ingame_template: np.ndarray | None = None
        unavailable_role_fingerprints: set[str] = set()
        unavailable_role_templates: list[np.ndarray] = []
        entry_failure_roles: list[dict[str, object]] = []
        unavailable_role_count = 0
        processed_role_templates: list[np.ndarray] = []
        processed_offset = int(os.environ.get("SGZZ_ROLE_IDENTITY_PROCESSED_OFFSET", "0"))
        processed_cycles = processed_offset
        daily_like_done_count = 0
        like_limit_stop_reached = False
        completion_reason = "cycle_limit"
        seed_run_dir_text = os.environ.get("SGZZ_ROLE_IDENTITY_SEED_RUN_DIR", "").strip()
        if seed_run_dir_text:
            seed_run_dir = Path(seed_run_dir_text)
            seed_specs = (
                ("row", "account_role_identity_row_01", "first_row_template"),
                ("title", "account_role_identity_title_01", "first_title_template"),
                ("ingame", "account_role_identity_ingame_01", "first_ingame_template"),
            )
            for kind, pattern, target_name in seed_specs:
                seed_path = next(iter(sorted(seed_run_dir.glob(f"*_{pattern}.png"))), None)
                seed_image = cv2.imread(str(seed_path)) if seed_path else None
                if target_name == "first_row_template":
                    first_row_template = seed_image
                elif target_name == "first_title_template":
                    first_title_template = seed_image
                else:
                    first_ingame_template = seed_image
                self._record(
                    {
                        "type": "state",
                        "state": "account_remaining_role_identity_seed",
                        "kind": kind,
                        "path": str(seed_path) if seed_path else None,
                        "loaded": seed_image is not None,
                    }
                )
        self._record(
            {
                "type": "state",
                "state": "account_remaining_role_resume_context",
                "processed_offset": processed_offset,
                "seed_run_dir": seed_run_dir_text or None,
            }
        )
        cycle = 1
        like_limit_consecutive_count = 0
        incomplete_role_retry_count = 0
        while cycle <= max_cycles:
            self._record(
                {
                    "type": "state",
                    "state": "account_remaining_role_cycle_iteration",
                    "iteration": cycle,
                    "max_cycles": max_cycles,
                }
            )
            try:
                self.switch_account_to_role_select()
                self.open_server_selector()
                if role_selection_order == "bottom":
                    self.scroll_server_selector_to_bottom()
                else:
                    self.scroll_server_selector_to_top()
                rows = self.detect_server_selector_role_rows()
                if not rows:
                    self.screenshot("account_remaining_roles_no_role_rows")
                    restored_hidden_role = self.restore_hidden_role_from_selector_if_available()
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_hidden_role_restore_attempt",
                            "restored": restored_hidden_role,
                        }
                    )
                    if not restored_hidden_role:
                        self._record(
                            {
                                "type": "state",
                                "state": "account_remaining_roles_no_visible_or_hidden_stop",
                                "processed_cycles": processed_cycles,
                            }
                        )
                        self._watchdog_reset()
                        self.screenshot("account_remaining_roles_no_visible_or_hidden_stop")
                        completion_reason = "no_visible_or_hidden_roles"
                        break

                    self.open_server_selector()
                    self.scroll_server_selector_to_bottom()
                    rows = self.detect_server_selector_role_rows()
                    if not rows:
                        self.screenshot("account_remaining_roles_no_rows_after_restore_hidden")
                        raise RuntimeError(
                            "Account remaining-role cycle restored a hidden role, but still could not detect role rows."
                        )

                selector_image = self.bot.screenshot_image()
                candidate_rows = list(reversed(rows)) if role_selection_order == "bottom" else rows
                selected_row: tuple[
                    dict[str, int | float],
                    tuple[int, int, int, int],
                    np.ndarray,
                    str,
                ] | None = None
                skipped_unavailable_rows = 0
                skipped_processed_rows = 0
                for candidate_row in candidate_rows:
                    candidate_region = self.server_selector_role_identity_region(
                        candidate_row,
                        selector_image,
                    )
                    candidate_crop = self._crop(selector_image, candidate_region).copy()
                    candidate_fingerprint = self.fingerprint_server_selector_role_row(
                        candidate_row,
                        selector_image,
                    )
                    unavailable_similarity = max(
                        (
                            self._template_similarity(candidate_crop, unavailable_template)
                            for unavailable_template in unavailable_role_templates
                        ),
                        default=0.0,
                    )
                    known_unavailable = bool(
                        (
                            candidate_fingerprint
                            and candidate_fingerprint in unavailable_role_fingerprints
                        )
                        or unavailable_similarity >= 0.97
                    )
                    if known_unavailable:
                        skipped_unavailable_rows += 1
                        self._record(
                            {
                                "type": "vision_feature",
                                "feature": "account_remaining_unavailable_role_row_skipped",
                                "iteration": cycle,
                                "row_y": int(candidate_row["y"]),
                                "tap_y": int(candidate_row["tap_y"]),
                                "fingerprint": candidate_fingerprint,
                                "row_similarity": round(unavailable_similarity, 4),
                            }
                        )
                        continue
                    processed_similarity = max(
                        (
                            self._template_similarity(candidate_crop, processed_template)
                            for processed_template in processed_role_templates
                        ),
                        default=0.0,
                    )
                    if processed_similarity >= 0.97:
                        skipped_processed_rows += 1
                        self._record(
                            {
                                "type": "vision_feature",
                                "feature": "account_remaining_processed_role_row_skipped",
                                "iteration": cycle,
                                "row_y": int(candidate_row["y"]),
                                "tap_y": int(candidate_row["tap_y"]),
                                "row_similarity": round(processed_similarity, 4),
                            }
                        )
                        continue
                    selected_row = (
                        candidate_row,
                        candidate_region,
                        candidate_crop,
                        candidate_fingerprint,
                    )
                    break

                if selected_row is None:
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_roles_all_classified_stop",
                            "iteration": cycle,
                            "processed_cycles": processed_cycles,
                            "role_row_count": len(rows),
                            "skipped_unavailable_rows": skipped_unavailable_rows,
                            "skipped_processed_rows": skipped_processed_rows,
                        }
                    )
                    self._watchdog_reset()
                    self.screenshot("account_remaining_roles_all_classified_stop")
                    completion_reason = "all_roles_classified"
                    break

                role_row, row_identity_region, row_identity_crop, role_fingerprint = selected_row
                row_identity_region = self.server_selector_role_identity_region(role_row, selector_image)
                row_identity_score = self.compare_role_identity_crop(
                    label="server_selector_selected_role_row",
                    image=selector_image,
                    region=row_identity_region,
                    template=first_row_template,
                )
                row_identity_path = self.save_crop(
                    f"account_role_identity_row_{cycle:02d}",
                    selector_image,
                    row_identity_region,
                )
                if first_row_template is None:
                    first_row_template = row_identity_crop.copy()
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_first_role_row_identity_recorded",
                            "path": str(row_identity_path),
                        }
                    )
                row_repeat_candidate = processed_cycles > 0 and row_identity_score >= row_repeat_threshold
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_remaining_selected_role",
                        "iteration": cycle,
                        "role_selection_order": role_selection_order,
                        "role_row_count": len(rows),
                        "row_x": int(role_row["x"]),
                        "row_y": int(role_row["y"]),
                        "tap_x": int(role_row["tap_x"]),
                        "tap_y": int(role_row["tap_y"]),
                        "inferred_selected": bool(role_row.get("inferred_selected", False)),
                        "fingerprint": role_fingerprint,
                        "row_identity_path": str(row_identity_path),
                        "row_identity_score": round(row_identity_score, 4),
                        "row_repeat_candidate": row_repeat_candidate,
                        "skipped_unavailable_rows": skipped_unavailable_rows,
                        "skipped_processed_rows": skipped_processed_rows,
                    }
                )

                point = Point(int(role_row["tap_x"]), int(role_row["tap_y"]))
                self.tap("本账号剩余角色-选择当前角色", point, wait_seconds=0.8)
                self.tap_server_selector_confirm("本账号剩余角色-确定当前角色", wait_seconds=1.5)
                title_screenshot_path = self.screenshot("after_account_remaining_select_role")
                title_image = cv2.imread(str(title_screenshot_path))
                if title_image is None:
                    title_image = self.bot.screenshot_image()
                title_identity_region = self.title_role_identity_region(title_image)
                title_identity_score = self.compare_role_identity_crop(
                    label="title_selected_role_server_id",
                    image=title_image,
                    region=title_identity_region,
                    template=first_title_template,
                )
                title_identity_path = self.save_crop(
                    f"account_role_identity_title_{cycle:02d}",
                    title_image,
                    title_identity_region,
                )
                title_identity_crop = self._crop(title_image, title_identity_region).copy()
                if first_title_template is None:
                    first_title_template = title_identity_crop.copy()
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_first_title_identity_recorded",
                            "path": str(title_identity_path),
                        }
                    )

                matching_entry_failure: dict[str, object] | None = None
                entry_failure_title_score = 0.0
                for entry_failure in entry_failure_roles:
                    failed_title_template = entry_failure.get("title_template")
                    if not isinstance(failed_title_template, np.ndarray):
                        continue
                    failure_score = self._template_similarity(
                        title_identity_crop,
                        failed_title_template,
                    )
                    if failure_score > entry_failure_title_score:
                        entry_failure_title_score = failure_score
                        matching_entry_failure = entry_failure
                if entry_failure_title_score < entry_failure_title_match_threshold:
                    matching_entry_failure = None

                title_repeat_candidate = processed_cycles > 0 and title_identity_score >= title_repeat_threshold
                title_repeat = title_repeat_candidate and row_repeat_candidate
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_remaining_title_role_identity",
                        "iteration": cycle,
                        "path": str(title_identity_path),
                        "score": round(title_identity_score, 4),
                        "row_repeat_candidate": row_repeat_candidate,
                        "title_repeat_candidate": title_repeat_candidate,
                        "repeat": title_repeat,
                        "entry_failure_title_score": round(entry_failure_title_score, 4),
                        "entry_failure_retry": matching_entry_failure is not None,
                    }
                )
                if title_repeat:
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_roles_repeated_title_identity_stop",
                            "processed_cycles": processed_cycles,
                            "row_identity_score": round(row_identity_score, 4),
                            "title_identity_score": round(title_identity_score, 4),
                        }
                    )
                    self._watchdog_reset()
                    self.screenshot("account_remaining_roles_repeated_title_identity_stop")
                    completion_reason = "repeated_title_identity"
                    break

                entry_attempt_limit = max(
                    2,
                    min(6, int(os.environ.get("SGZZ_ROLE_ENTRY_ATTEMPTS", "4"))),
                )
                role_entry_ready = False
                for entry_attempt in range(1, entry_attempt_limit + 1):
                    if entry_attempt == 1:
                        self.enter_selected_server(wait_seconds=8.0)
                    else:
                        self.click_title_enter_if_present(
                            timeout_seconds=0.6,
                            click_login_after_prompt=True,
                        )

                    quick_login_closed = self.close_xiaomi_quick_login_prompt_if_present(
                        timeout_seconds=1.0
                    )
                    notice_closed = self.close_notice_ack_if_present()
                    entry_image = self.bot.screenshot_image()
                    entry_marker_key, entry_marker = self._detect_account_role_select_entry_marker(
                        entry_image,
                        source=f"account_remaining_role_entry_attempt_{entry_attempt}",
                    )
                    still_on_title = (
                        entry_marker_key in {"title_select_server", "title_enter_button"}
                        and entry_marker is not None
                    )
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_role_entry_check",
                            "iteration": cycle,
                            "attempt": entry_attempt,
                            "quick_login_closed": quick_login_closed,
                            "notice_closed": notice_closed,
                            "still_on_title": still_on_title,
                            "marker": entry_marker_key,
                            "marker_score": round(entry_marker.score, 4) if entry_marker else 0.0,
                        }
                    )
                    if not still_on_title:
                        role_entry_ready = True
                        break

                if not role_entry_ready:
                    if matching_entry_failure is None:
                        matching_entry_failure = {
                            "title_template": title_identity_crop.copy(),
                            "title_identity_path": str(title_identity_path),
                            "failure_batches": 0,
                            "row_templates": [],
                            "fingerprints": set(),
                        }
                        entry_failure_roles.append(matching_entry_failure)
                    failure_batches = int(matching_entry_failure.get("failure_batches", 0)) + 1
                    matching_entry_failure["failure_batches"] = failure_batches
                    failed_row_templates = matching_entry_failure.get("row_templates")
                    if not isinstance(failed_row_templates, list):
                        failed_row_templates = []
                        matching_entry_failure["row_templates"] = failed_row_templates
                    failed_row_templates.append(row_identity_crop.copy())
                    failed_fingerprints = matching_entry_failure.get("fingerprints")
                    if not isinstance(failed_fingerprints, set):
                        failed_fingerprints = set()
                        matching_entry_failure["fingerprints"] = failed_fingerprints
                    if role_fingerprint:
                        failed_fingerprints.add(role_fingerprint)

                    classify_unavailable = failure_batches >= 2
                    if classify_unavailable:
                        unavailable_role_fingerprints.update(failed_fingerprints)
                        unavailable_role_templates.extend(failed_row_templates)
                        unavailable_role_count += 1
                        entry_failure_roles.remove(matching_entry_failure)
                    self._record(
                        {
                            "type": "state",
                            "state": (
                                "account_remaining_role_classified_unavailable"
                                if classify_unavailable
                                else "account_remaining_role_entry_retry_deferred"
                            ),
                            "iteration": cycle,
                            "processed_cycles": processed_cycles,
                            "fingerprint": role_fingerprint,
                            "entry_attempt_limit": entry_attempt_limit,
                            "failure_batches": failure_batches,
                            "total_entry_attempts": failure_batches * entry_attempt_limit,
                            "entry_failure_title_score": round(entry_failure_title_score, 4),
                            "reason": "title_screen_remained_after_entry_retries",
                            "title_marker_confirmed_each_attempt": True,
                            "row_identity_path": str(row_identity_path),
                            "title_identity_path": str(title_identity_path),
                            "action": (
                                "skip_classified_unavailable_role_and_continue"
                                if classify_unavailable
                                else "retry_same_role_before_classifying_unavailable"
                            ),
                        }
                    )
                    self._watchdog_reset()
                    self.screenshot(
                        "account_remaining_role_classified_unavailable"
                        if classify_unavailable
                        else "account_remaining_role_entry_retry_deferred"
                    )
                    continue

                if matching_entry_failure is not None:
                    failure_batches = int(matching_entry_failure.get("failure_batches", 0))
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_role_entry_recovered_after_retry",
                            "iteration": cycle,
                            "processed_cycles": processed_cycles,
                            "failure_batches": failure_batches,
                            "entry_failure_title_score": round(entry_failure_title_score, 4),
                            "title_identity_path": str(title_identity_path),
                        }
                    )
                    entry_failure_roles.remove(matching_entry_failure)

                self.handle_entry_preconditions(max_rounds=8)
                self.close_signin_reward_if_present(timeout_seconds=2.0)
                self.handle_entry_preconditions(max_rounds=4)

                ingame_image = self.bot.screenshot_image()
                ingame_identity_region = self.ingame_role_identity_region(ingame_image)
                ingame_identity_score = self.compare_role_identity_crop(
                    label="ingame_top_left_role_name",
                    image=ingame_image,
                    region=ingame_identity_region,
                    template=first_ingame_template,
                )
                ingame_identity_path = self.save_crop(
                    f"account_role_identity_ingame_{cycle:02d}",
                    ingame_image,
                    ingame_identity_region,
                )
                if first_ingame_template is None:
                    first_ingame_template = self._crop(ingame_image, ingame_identity_region).copy()
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_first_ingame_identity_recorded",
                            "path": str(ingame_identity_path),
                        }
                    )
                ingame_repeat = processed_cycles > 0 and ingame_identity_score >= ingame_repeat_threshold
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "account_remaining_ingame_role_identity",
                        "iteration": cycle,
                        "path": str(ingame_identity_path),
                        "score": round(ingame_identity_score, 4),
                        "repeat": ingame_repeat,
                    }
                )
                if ingame_repeat:
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_roles_repeated_ingame_identity_stop",
                            "processed_cycles": processed_cycles,
                            "ingame_identity_score": round(ingame_identity_score, 4),
                        }
                    )
                    self._watchdog_reset()
                    self.screenshot("account_remaining_roles_repeated_ingame_identity_stop")
                    completion_reason = "repeated_ingame_identity"
                    break

                self.run_daily_signin_like_gacha(
                    include_gacha=include_gacha,
                    include_gamecircle_signin=include_gamecircle_signin,
                )
                if not self._last_daily_like_done:
                    incomplete_role_retry_count += 1
                    self._record(
                        {
                            "type": "state",
                            "state": "account_remaining_role_flow_incomplete_not_marked",
                            "iteration": cycle,
                            "processed_cycles": processed_cycles,
                            "daily_like_done_count": daily_like_done_count,
                            "like_limit_reached": self._last_like_limit_reached,
                            "reason": "daily_like_not_completed",
                            "row_identity_path": str(row_identity_path),
                            "retry_count": incomplete_role_retry_count,
                            "retry_limit": incomplete_role_retry_limit,
                        }
                    )
                    self._watchdog_reset()
                    self.screenshot("account_remaining_role_flow_incomplete_not_marked")
                    if incomplete_role_retry_count <= incomplete_role_retry_limit:
                        self._record(
                            {
                                "type": "state",
                                "state": "account_remaining_role_flow_retry_wait",
                                "iteration": cycle,
                                "processed_cycles": processed_cycles,
                                "retry_count": incomplete_role_retry_count,
                                "retry_limit": incomplete_role_retry_limit,
                                "wait_seconds": incomplete_role_retry_wait_seconds,
                                "action": "retry_same_unprocessed_role",
                            }
                        )
                        self._sleep_with_watchdog(
                            incomplete_role_retry_wait_seconds,
                            source="account_remaining_role_flow_retry_wait",
                        )
                        self._watchdog_reset()
                        continue
                    completion_reason = "role_flow_incomplete"
                    break
                processed_role_templates.append(row_identity_crop.copy())
                incomplete_role_retry_count = 0
                processed_cycles += 1
                self._watchdog_mark_forward_progress(
                    source="account_remaining_role_completed"
                )
                if self._last_daily_like_done:
                    daily_like_done_count += 1
                if self._last_like_limit_reached:
                    like_limit_consecutive_count += 1
                else:
                    like_limit_consecutive_count = 0
                self._record(
                    {
                        "type": "state",
                        "state": "account_remaining_role_like_limit_check",
                        "iteration": cycle,
                            "processed_cycles": processed_cycles,
                            "daily_like_done_count": daily_like_done_count,
                            "like_limit_reached": self._last_like_limit_reached,
                            "like_limit_consecutive_count": like_limit_consecutive_count,
                            "like_limit_stop_threshold": like_limit_stop_threshold,
                    }
                )
                cycle += 1
            except SGZZScreenStuckRestart as exc:
                self._record(
                    {
                        "type": "state",
                        "state": "account_remaining_role_cycle_retry_after_stuck",
                        "iteration": cycle,
                        "processed_cycles": processed_cycles,
                        "restart_count": self._watchdog_restarts,
                        "error": str(exc),
                    }
                )
                continue
        else:
            self._record(
                {
                    "type": "state",
                    "state": "account_remaining_roles_cycle_limit_reached",
                    "max_cycles": max_cycles,
                }
            )

        processed_this_run = max(0, processed_cycles - processed_offset)
        classified_this_run = processed_this_run + unavailable_role_count
        account_like_completed = classified_this_run > 0 and (
            completion_reason in {"all_roles_classified", "no_visible_or_hidden_roles"}
            and daily_like_done_count >= processed_this_run
        )
        self._last_account_cycle_summary = {
            "processed_cycles": processed_cycles,
            "processed_offset": processed_offset,
            "processed_this_run": processed_this_run,
            "unavailable_role_count": unavailable_role_count,
            "classified_this_run": classified_this_run,
            "daily_like_done_count": daily_like_done_count,
            "like_limit_stop_reached": like_limit_stop_reached,
            "like_limit_consecutive_count": like_limit_consecutive_count,
            "like_limit_stop_threshold": like_limit_stop_threshold,
            "completion_reason": completion_reason,
            "account_like_completed": account_like_completed,
            "max_cycles": max_cycles,
        }
        self._record(
            {
                "type": "state",
                "state": "account_remaining_roles_daily_cycle_done",
                **self._last_account_cycle_summary,
            }
        )
        return self.screenshot("after_account_remaining_roles_daily_cycle")

    def run_configured_account_remaining_roles_daily_cycle(
        self,
        credential: SGZZAccountCredential,
        *,
        account_index: int,
        account_count: int,
        max_cycles: int,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
        process_current_role_before_switch: bool = False,
    ) -> Path:
        self._record(
            {
                "type": "state",
                "state": "account_batch_configured_account_login_start",
                "index": account_index,
                "account_count": account_count,
                "line_number": credential.line_number,
                "account": credential.masked_account,
                "client": credential.client,
                "package": credential.package,
                "max_cycles": max_cycles,
                "include_gacha": include_gacha,
                "include_gamecircle_signin": include_gamecircle_signin,
                "process_current_role_before_switch": process_current_role_before_switch,
            }
        )
        self._watchdog_reset()
        self.login_configured_account(
            credential,
            process_current_role_before_switch=process_current_role_before_switch,
            include_gacha=include_gacha,
            include_gamecircle_signin=include_gamecircle_signin,
        )
        self._record(
            {
                "type": "state",
                "state": "account_batch_configured_account_login_done",
                "index": account_index,
                "account_count": account_count,
                "account": credential.masked_account,
                "client": credential.client,
                "package": credential.package,
            }
        )

        account_done_path = self.run_account_remaining_roles_daily_cycle(
            max_cycles=max_cycles,
            include_gacha=include_gacha,
            include_gamecircle_signin=include_gamecircle_signin,
        )
        account_cycle_summary = dict(self._last_account_cycle_summary)
        self._record(
            {
                "type": "state",
                "state": "account_batch_configured_account_roles_done",
                "index": account_index,
                "account_count": account_count,
                "account": credential.masked_account,
                "client": credential.client,
                "package": credential.package,
                "record_path": str(account_done_path),
                **account_cycle_summary,
            }
        )
        self._watchdog_reset()
        return account_done_path

    def run_account_batch_remaining_roles_daily_cycle(
        self,
        *,
        accounts_file: str | Path | None = None,
        max_cycles_per_account: int = 20,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
    ) -> Path:
        if max_cycles_per_account < 1:
            raise ValueError("Account batch role cycle count must be at least 1.")

        account_path = resolve_sgzz_accounts_file(accounts_file)
        credentials = load_sgzz_account_credentials(account_path)
        self.select_account_client(credentials[0], restart_if_changed=False)
        process_bootstrap_current_role = os.environ.get(
            "SGZZ_PROCESS_BOOTSTRAP_CURRENT_ROLE",
            "0",
        ).lower() not in {"0", "false", "off", "no"}
        self._record(
            {
                "type": "state",
                "state": "run_account_batch_remaining_roles_daily_cycle",
                "accounts_file": str(account_path),
                "account_count": len(credentials),
                "max_cycles_per_account": max_cycles_per_account,
                "include_gacha": include_gacha,
                "include_gamecircle_signin": include_gamecircle_signin,
                "process_bootstrap_current_role": process_bootstrap_current_role,
                "accounts": [
                    {
                        "account": credential.masked_account,
                        "client": credential.client,
                        "package": credential.package,
                    }
                    for credential in credentials
                ],
                "strategy": "bootstrap_current_role_then_config_order_login_each_account_all_roles",
            }
        )
        self._record(
            {
                "type": "state",
                "state": "account_batch_initial_restart",
                "client": self.client_name,
                "package": self.package,
            }
        )
        self.bot.client.force_stop_package(self.package)
        self._sleep_with_watchdog(1.0, source="account_batch_initial_restart")
        self.launch(wait_seconds=8.0)
        self.screenshot("before_account_batch_remaining_roles_daily_cycle")

        previous_offset = os.environ.pop("SGZZ_ROLE_IDENTITY_PROCESSED_OFFSET", None)
        previous_seed = os.environ.pop("SGZZ_ROLE_IDENTITY_SEED_RUN_DIR", None)
        try:
            for index, credential in enumerate(credentials, start=1):
                self.select_account_client(credential, restart_if_changed=True)
                for attempt in range(1, self._watchdog_restart_limit + 2):
                    os.environ.pop("SGZZ_ROLE_IDENTITY_PROCESSED_OFFSET", None)
                    os.environ.pop("SGZZ_ROLE_IDENTITY_SEED_RUN_DIR", None)
                    if index == 1 and attempt == 1:
                        if previous_offset is not None:
                            os.environ["SGZZ_ROLE_IDENTITY_PROCESSED_OFFSET"] = previous_offset
                        if previous_seed is not None:
                            os.environ["SGZZ_ROLE_IDENTITY_SEED_RUN_DIR"] = previous_seed
                    self._record(
                        {
                            "type": "state",
                            "state": "account_batch_account_start",
                            "index": index,
                            "account_count": len(credentials),
                            "line_number": credential.line_number,
                            "account": credential.masked_account,
                            "account_key": credential.account_key,
                            "client": credential.client,
                            "package": credential.package,
                            "attempt": attempt,
                        }
                    )
                    try:
                        account_done_path = self.run_configured_account_remaining_roles_daily_cycle(
                            credential,
                            account_index=index,
                            account_count=len(credentials),
                            max_cycles=max_cycles_per_account,
                            include_gacha=include_gacha,
                            include_gamecircle_signin=include_gamecircle_signin,
                            process_current_role_before_switch=(
                                process_bootstrap_current_role
                                and index == 1
                                and attempt == 1
                            ),
                        )
                    except SGZZScreenStuckRestart as exc:
                        self._record(
                            {
                                "type": "state",
                                "state": "account_batch_retry_after_stuck",
                                "index": index,
                                "account": credential.masked_account,
                                "account_key": credential.account_key,
                                "line_number": credential.line_number,
                                "attempt": attempt,
                                "restart_count": self._watchdog_restarts,
                                "error": str(exc),
                            }
                        )
                        continue

                    account_cycle_summary = dict(self._last_account_cycle_summary)
                    if not bool(account_cycle_summary.get("account_like_completed")):
                        self._record(
                            {
                                "type": "state",
                                "state": "account_batch_account_incomplete_halt",
                                "index": index,
                                "account_count": len(credentials),
                                "account": credential.masked_account,
                                "account_key": credential.account_key,
                                "line_number": credential.line_number,
                                "client": credential.client,
                                "package": credential.package,
                                "record_path": str(account_done_path),
                                "action": "stop_without_switching_to_next_account",
                                **account_cycle_summary,
                            }
                        )
                        raise RuntimeError(
                            f"Account {credential.masked_account} is incomplete "
                            f"({account_cycle_summary.get('completion_reason', 'unknown')}); "
                            "refusing to switch to the next account."
                        )

                    self._record(
                        {
                            "type": "state",
                            "state": "account_batch_account_done",
                            "index": index,
                            "account_count": len(credentials),
                            "account": credential.masked_account,
                            "account_key": credential.account_key,
                            "line_number": credential.line_number,
                            "client": credential.client,
                            "package": credential.package,
                            "record_path": str(account_done_path),
                            **account_cycle_summary,
                        }
                    )
                    if index < len(credentials):
                        next_credential = credentials[index]
                        self._record(
                            {
                                "type": "state",
                                "state": "account_batch_prepare_next_configured_account_login",
                                "finished_index": index,
                                "next_index": index + 1,
                                "account_count": len(credentials),
                                "finished_account": credential.masked_account,
                                "finished_account_key": credential.account_key,
                                "next_account": next_credential.masked_account,
                                "next_account_key": next_credential.account_key,
                                "next_line_number": next_credential.line_number,
                                "next_client": next_credential.client,
                                "next_package": next_credential.package,
                            }
                        )
                        self._watchdog_reset()
                        if next_credential.package == credential.package:
                            try:
                                self.open_account_login_modal_for_switch(
                                    include_gacha=include_gacha,
                                    include_gamecircle_signin=include_gamecircle_signin,
                                )
                            except SGZZScreenStuckRestart as exc:
                                self._record(
                                    {
                                        "type": "state",
                                        "state": "account_batch_prepare_next_retry_after_stuck",
                                        "finished_index": index,
                                        "next_index": index + 1,
                                        "next_account": next_credential.masked_account,
                                        "next_account_key": next_credential.account_key,
                                        "restart_count": self._watchdog_restarts,
                                        "error": str(exc),
                                    }
                                )
                        else:
                            self._record(
                                {
                                    "type": "state",
                                    "state": "account_batch_prepare_next_client_switch",
                                    "finished_index": index,
                                    "next_index": index + 1,
                                    "next_account": next_credential.masked_account,
                                    "next_account_key": next_credential.account_key,
                                    "next_client": next_credential.client,
                                    "next_package": next_credential.package,
                                }
                            )
                        self._record(
                            {
                                "type": "state",
                                "state": "account_batch_next_configured_account_login_ready",
                                "next_index": index + 1,
                                "account_count": len(credentials),
                                "next_account": next_credential.masked_account,
                                "next_account_key": next_credential.account_key,
                                "next_client": next_credential.client,
                                "next_package": next_credential.package,
                            }
                        )
                    break
                else:
                    raise RuntimeError(
                        f"Account batch flow could not complete {credential.masked_account} "
                        f"after {self._watchdog_restart_limit + 1} stuck recoveries."
                    )
        finally:
            if previous_offset is not None:
                os.environ["SGZZ_ROLE_IDENTITY_PROCESSED_OFFSET"] = previous_offset
            if previous_seed is not None:
                os.environ["SGZZ_ROLE_IDENTITY_SEED_RUN_DIR"] = previous_seed

        self._record(
            {
                "type": "state",
                "state": "account_batch_remaining_roles_daily_cycle_done",
                "account_count": len(credentials),
                "accounts": [
                    {
                        "account": credential.masked_account,
                        "client": credential.client,
                        "package": credential.package,
                    }
                    for credential in credentials
                ],
            }
        )
        return self.screenshot("after_account_batch_remaining_roles_daily_cycle")

    def open_friends_list_for_like(self) -> Path:
        self._record({"type": "state", "state": "open_friends_list_for_like"})
        self.screenshot("before_like_open_friends_list")
        self.close_known_retreat_if_present(timeout_seconds=self._fast_timeout(0.8, 0.25))
        if not self.detect_like_main_screen():
            self.screenshot("like_open_friends_list_not_main_screen")
            raise RuntimeError("Like flow expected game main screen, but green recruit button was not found.")
        self.handle_main_blocking_troop_prompt_if_present(
            timeout_seconds=self._fast_timeout(0.8, 0.25),
        )
        if not self.detect_like_main_screen():
            recovered = self.recover_to_main_screen(max_steps=4)
            self._record(
                {
                    "type": "state",
                    "state": "like_open_friends_list_recover_after_troop_prompt",
                    "recovered": recovered,
                }
            )
            if not recovered:
                self.screenshot("like_open_friends_list_not_main_after_troop_prompt")
                raise RuntimeError("Like flow could not return to main screen after troop guide prompt.")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        region = (0, int(h * 0.72), int(w * 0.24), int(h * 0.14))
        friends = self._find_template_in_image(
            image,
            "main_friend_button",
            threshold=0.68,
            region=region,
        )
        if not friends and not self.fast_mode:
            friends = self.wait_for_template(
                "点赞流程-好友按钮",
                "main_friend_button",
                timeout_seconds=1.0,
                threshold=0.68,
                region=region,
            )
        if friends:
            point = Point(*friends.center)
            source = "template"
            score = round(friends.score, 4)
        else:
            point = self.coords.portrait_friend_button
            source = "fallback"
            score = 0.0

        self._record(
            {
                "type": "vision_feature",
                "feature": "like_friend_button",
                "source": source,
                "x": point.x,
                "y": point.y,
                "score": score,
            }
        )
        self.tap("点赞流程-打开好友列表", point, wait_seconds=self._fast_wait(1.5, 0.85))
        friend_card_region = (0, int(h * 0.16), int(w * 0.32), int(h * 0.68))
        friend_back_region = (0, int(h * 0.90), int(w * 0.30), int(h * 0.10))
        opened = self.wait_for_template(
            "点赞流程-好友列表打开复查",
            "like_dabai_friend_card",
            timeout_seconds=self._fast_timeout(0.8, 0.35),
            threshold=0.72,
            region=friend_card_region,
        )
        friend_page = self.wait_for_template(
            "点赞流程-好友列表页面复查",
            "like_friends_back_button",
            timeout_seconds=self._fast_timeout(0.4, 0.20),
            threshold=0.70,
            region=friend_back_region,
        )
        self._record(
            {
                "type": "vision_feature",
                "feature": "like_friend_list_after_open",
                "present": opened is not None,
                "friend_page_present": friend_page is not None,
                "x": opened.x if opened else None,
                "y": opened.y if opened else None,
                "width": opened.width if opened else None,
                "height": opened.height if opened else None,
                "score": round(opened.score, 4) if opened else 0.0,
            }
        )
        if not opened and not friend_page:
            self.tap("点赞流程-打开好友列表-重试", point, wait_seconds=self._fast_wait(1.8, 1.0))
            retry_image = self.bot.screenshot_image()
            retry_h, retry_w = retry_image.shape[:2]
            retry_card_region = (0, int(retry_h * 0.16), int(retry_w * 0.32), int(retry_h * 0.68))
            retry_back_region = (0, int(retry_h * 0.90), int(retry_w * 0.30), int(retry_h * 0.10))
            opened = self._find_template_in_image(
                retry_image,
                "like_dabai_friend_card",
                threshold=0.72,
                region=retry_card_region,
            )
            friend_page = self._find_template_in_image(
                retry_image,
                "like_friends_back_button",
                threshold=0.70,
                region=retry_back_region,
            )
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "like_friend_list_after_retry",
                    "present": opened is not None,
                    "friend_page_present": friend_page is not None,
                    "x": opened.x if opened else None,
                    "y": opened.y if opened else None,
                    "width": opened.width if opened else None,
                    "height": opened.height if opened else None,
                    "score": round(opened.score, 4) if opened else 0.0,
                }
            )

        if not opened and not friend_page:
            if self.handle_main_blocking_troop_prompt_if_present(
                timeout_seconds=self._fast_timeout(1.0, 0.35),
                max_taps=2,
            ):
                if not self.detect_like_main_screen():
                    self.recover_to_main_screen(max_steps=4)
                image = self.bot.screenshot_image()
                h, w = image.shape[:2]
                region = (0, int(h * 0.72), int(w * 0.24), int(h * 0.14))
                friends = self._find_template_in_image(
                    image,
                    "main_friend_button",
                    threshold=0.68,
                    region=region,
                )
                retry_point = Point(*friends.center) if friends else self.coords.portrait_friend_button
                self.tap(
                    "点赞流程-部队引导后打开好友列表",
                    retry_point,
                    wait_seconds=self._fast_wait(1.8, 1.0),
                )
                retry_image = self.bot.screenshot_image()
                retry_h, retry_w = retry_image.shape[:2]
                retry_card_region = (0, int(retry_h * 0.16), int(retry_w * 0.32), int(retry_h * 0.68))
                retry_back_region = (0, int(retry_h * 0.90), int(retry_w * 0.30), int(retry_h * 0.10))
                opened = self._find_template_in_image(
                    retry_image,
                    "like_dabai_friend_card",
                    threshold=0.72,
                    region=retry_card_region,
                )
                friend_page = self._find_template_in_image(
                    retry_image,
                    "like_friends_back_button",
                    threshold=0.70,
                    region=retry_back_region,
                )
                self._record(
                    {
                        "type": "vision_feature",
                        "feature": "like_friend_list_after_troop_prompt",
                        "present": opened is not None,
                        "friend_page_present": friend_page is not None,
                        "x": opened.x if opened else None,
                        "y": opened.y if opened else None,
                        "width": opened.width if opened else None,
                        "height": opened.height if opened else None,
                        "score": round(opened.score, 4) if opened else 0.0,
                    }
                )

        if not opened and not friend_page:
            self.screenshot("like_friend_list_open_failed")
            raise RuntimeError("Like flow could not open friend list before locating friend card.")
        return self.screenshot("after_like_open_friends_list")

    def close_friend_query_add_modal_if_present(self, *, timeout_seconds: float = 0.8) -> bool:
        self._record({"type": "state", "state": "close_friend_query_add_modal_if_present"})
        end_at = time() + max(0.1, timeout_seconds)
        while time() < end_at:
            image = self.bot.screenshot_image()
            h, w = image.shape[:2]
            close_region = (int(w * 0.82), int(h * 0.26), int(w * 0.16), int(h * 0.10))
            close_button = self._find_red_dot(image, close_region)
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "friend_query_add_close_button",
                    "present": close_button is not None,
                    "region_x": close_region[0],
                    "region_y": close_region[1],
                    "region_width": close_region[2],
                    "region_height": close_region[3],
                    "x": close_button.x if close_button else None,
                    "y": close_button.y if close_button else None,
                    "width": close_button.width if close_button else None,
                    "height": close_button.height if close_button else None,
                    "score": round(close_button.score, 1) if close_button else 0.0,
                }
            )
            if close_button:
                point = Point(*close_button.center)
                self.tap("点赞流程-关闭查询添加弹窗", point, wait_seconds=1.0)
                return True
            self._sleep_with_watchdog(0.2, source="close_friend_query_add_modal")
        return False

    def request_missing_like_friend(self, *, query_id: str | None = None) -> bool:
        query_id = resolve_sgzz_like_target_query_id(query_id)
        self._record(
            {
                "type": "state",
                "state": "request_missing_like_friend",
                "query_id": query_id,
            }
        )
        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        back_button = self._find_template_in_image(
            image,
            "like_friends_back_button",
            threshold=0.70,
            region=(0, int(h * 0.90), int(w * 0.30), int(h * 0.10)),
        )
        if not back_button:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "like_missing_friend_query",
                    "present": False,
                    "reason": "friend_list_not_visible",
                }
            )
            return False

        search_region = (0, int(h * 0.74), int(w * 0.28), int(h * 0.14))
        search_icon = self._find_template_in_image(
            image,
            "like_friend_search_icon",
            threshold=0.68,
            region=search_region,
        )
        search_point = Point(*search_icon.center) if search_icon else Point(int(w * 0.143), int(h * 0.811))
        self._record(
            {
                "type": "vision_feature",
                "feature": "like_friend_search_icon",
                "present": search_icon is not None,
                "source": "template" if search_icon else "friend_page_coordinate",
                "score": round(search_icon.score, 4) if search_icon else 0.0,
                "tap_x": search_point.x,
                "tap_y": search_point.y,
            }
        )
        self.tap("点赞流程-打开查询添加", search_point, wait_seconds=self._fast_wait(1.2, 0.8))

        dialog_region = (int(w * 0.28), int(h * 0.27), int(w * 0.46), int(h * 0.08))
        dialog = self.wait_for_template(
            "点赞流程-查询添加弹窗",
            "like_friend_query_title",
            timeout_seconds=self._fast_timeout(2.5, 1.2),
            threshold=0.68,
            region=dialog_region,
        )
        if not dialog:
            self.screenshot("like_friend_query_dialog_not_found")
            return False

        try:
            input_point = Point(int(w * 0.41), int(h * 0.356))
            self.tap("点赞流程-查询编号输入框", input_point, wait_seconds=0.25)
            self.clear_focused_text(max_chars=24)
            self.bot.client.input_text(query_id)
            self._record(
                {
                    "type": "state",
                    "state": "like_friend_query_id_entered",
                    "query_id": query_id,
                }
            )
            self._sleep_with_watchdog(0.35, source="like_friend_query_input")
            keyboard_image = self.bot.screenshot_image()
            if self.detect_soft_keyboard_visible(keyboard_image):
                self.bot.client.keyevent("KEYCODE_BACK")
                self._sleep_with_watchdog(0.5, source="like_friend_query_hide_keyboard")

            image = self.bot.screenshot_image()
            search_button = self._find_template_in_image(
                image,
                "like_friend_search_button",
                threshold=0.68,
                region=(int(w * 0.68), int(h * 0.31), int(w * 0.28), int(h * 0.10)),
            )
            search_button_point = (
                Point(*search_button.center)
                if search_button
                else Point(int(w * 0.83), int(h * 0.357))
            )
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "like_friend_search_button",
                    "present": search_button is not None,
                    "source": "template" if search_button else "query_dialog_coordinate",
                    "score": round(search_button.score, 4) if search_button else 0.0,
                    "tap_x": search_button_point.x,
                    "tap_y": search_button_point.y,
                }
            )
            self.tap(
                "点赞流程-查询添加搜索",
                search_button_point,
                wait_seconds=self._fast_wait(1.5, 1.0),
            )

            search_started_at = time()
            deadline = search_started_at + 10.0
            search_retried = False
            result_region = (int(w * 0.16), int(h * 0.38), int(w * 0.60), int(h * 0.13))
            button_region = (int(w * 0.68), int(h * 0.38), int(w * 0.28), int(h * 0.13))
            while time() < deadline:
                result_image = self.bot.screenshot_image()
                result = self._find_template_in_image(
                    result_image,
                    "like_friend_search_result_dabai",
                    threshold=0.66,
                    region=result_region,
                )
                add_button_candidate = self._find_template_in_image(
                    result_image,
                    "like_friend_add_button",
                    threshold=0.0,
                    region=button_region,
                )
                pending_button_candidate = self._find_template_in_image(
                    result_image,
                    "like_friend_add_pending_button",
                    threshold=0.0,
                    region=button_region,
                )
                add_button = (
                    add_button_candidate
                    if add_button_candidate and add_button_candidate.score >= 0.72
                    else None
                )
                pending_button = (
                    pending_button_candidate
                    if pending_button_candidate and pending_button_candidate.score >= 0.72
                    else None
                )
                if result and add_button:
                    point = Point(*add_button.center)
                    self._record(
                        {
                            "type": "vision_feature",
                            "feature": "like_friend_add_button",
                            "present": True,
                            "score": round(add_button.score, 4),
                            "tap_x": point.x,
                            "tap_y": point.y,
                        }
                    )
                    self.tap("点赞流程-发送好友申请", point, wait_seconds=self._fast_wait(1.4, 0.9))
                    confirmation_image = self.bot.screenshot_image()
                    sent_toast = self._find_template_in_image(
                        confirmation_image,
                        "like_friend_request_sent_toast",
                        threshold=0.68,
                        region=(int(w * 0.18), int(h * 0.20), int(w * 0.64), int(h * 0.10)),
                    )
                    pending_after_tap = self._find_template_in_image(
                        confirmation_image,
                        "like_friend_add_pending_button",
                        threshold=0.72,
                        region=button_region,
                    )
                    confirmed = sent_toast is not None or pending_after_tap is not None
                    self._record(
                        {
                            "type": "state",
                            "state": "like_friend_request_sent",
                            "confirmed": confirmed,
                            "source": "toast" if sent_toast else "pending_button" if pending_after_tap else "none",
                        }
                    )
                    self.screenshot(
                        "after_like_friend_request_sent"
                        if confirmed
                        else "like_friend_request_sent_unconfirmed"
                    )
                    # The subsequent friend-list lookup is the authoritative check.
                    # Retry it even when transient toast/button styling cannot confirm
                    # the request immediately.
                    return True
                if result and pending_button:
                    self._record(
                        {
                            "type": "state",
                            "state": "like_friend_request_already_pending",
                            "query_id": query_id,
                            "score": round(pending_button.score, 4),
                        }
                    )
                    self.screenshot("like_friend_request_already_pending")
                    return True
                if result:
                    # The queried target is unambiguous, but client skins can render
                    # the add/pending control differently. Clicking only inside the
                    # exact result row is safe; the later friend-list retry still
                    # decides whether the role can be marked complete.
                    point = Point(
                        button_region[0] + button_region[2] // 2,
                        button_region[1] + button_region[3] // 2,
                    )
                    self._record(
                        {
                            "type": "vision_feature",
                            "feature": "like_friend_result_action_fallback",
                            "result_score": round(result.score, 4),
                            "add_button_score": round(add_button_candidate.score, 4)
                            if add_button_candidate
                            else 0.0,
                            "pending_button_score": round(pending_button_candidate.score, 4)
                            if pending_button_candidate
                            else 0.0,
                            "tap_x": point.x,
                            "tap_y": point.y,
                        }
                    )
                    self.tap(
                        "点赞流程-查询结果操作按钮-样式兜底",
                        point,
                        wait_seconds=self._fast_wait(1.4, 0.9),
                    )
                    self.screenshot("after_like_friend_result_action_fallback")
                    return True
                if not search_retried and time() - search_started_at >= 2.5:
                    self.tap(
                        "点赞流程-查询添加搜索-重试",
                        search_button_point,
                        wait_seconds=self._fast_wait(1.2, 0.8),
                    )
                    search_retried = True
                self._sleep_with_watchdog(0.4, source="wait_like_friend_search_result")

            self._record(
                {
                    "type": "state",
                    "state": "like_friend_search_result_not_found",
                    "query_id": query_id,
                }
            )
            self.screenshot("like_friend_search_result_not_found")
            return False
        finally:
            self.close_friend_query_add_modal_if_present(timeout_seconds=1.5)

    def click_dabai_friend_button_for_like(self) -> Path:
        self._record({"type": "state", "state": "click_dabai_friend_button_for_like"})
        self.screenshot("before_like_click_dabai_friend_button")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        card_region = (0, int(h * 0.16), int(w * 0.32), int(h * 0.68))
        card = self.wait_for_template(
            "点赞流程-大白丨二大大好友卡片",
            "like_dabai_friend_card",
            timeout_seconds=self._fast_timeout(2.0, 0.8),
            threshold=0.72,
            region=card_region,
        )
        if not card:
            self.screenshot("like_dabai_friend_card_not_found")
            raise RuntimeError("Like flow could not find friend card: 大白丨二大大.")

        self._record(
            {
                "type": "vision_feature",
                "feature": "like_dabai_friend_card",
                "source": "template",
                "x": card.x,
                "y": card.y,
                "width": card.width,
                "height": card.height,
                "score": round(card.score, 4),
            }
        )

        button_region = (
            max(0, card.x + int(card.width * 0.55)),
            max(0, card.y + int(card.height * 0.02)),
            min(w - card.x, int(card.width * 0.44)),
            min(h - card.y, int(card.height * 0.50)),
        )
        button = self.wait_for_template(
            "点赞流程-大白丨二大大头像旁按钮",
            "like_dabai_friend_button",
            timeout_seconds=self._fast_timeout(0.8, 0.35),
            threshold=0.50,
            region=button_region,
        )
        if button:
            point = Point(*button.center)
            source = "button_template"
            score = round(button.score, 4)
        else:
            point = Point(int(card.x + card.width * 0.78), int(card.y + card.height * 0.31))
            source = "card_relative"
            score = 0.0

        self._record(
            {
                "type": "vision_feature",
                "feature": "like_dabai_friend_side_button",
                "source": source,
                "x": point.x,
                "y": point.y,
                "score": score,
                "card_x": card.x,
                "card_y": card.y,
                "card_width": card.width,
                "card_height": card.height,
            }
        )
        self.tap("点赞流程-点击大白丨二大大头像旁按钮", point, wait_seconds=self._fast_wait(1.2, 0.75))
        return self.screenshot("after_like_click_dabai_friend_button")

    def click_personal_info_button_for_like(self) -> Path:
        self._record({"type": "state", "state": "click_personal_info_button_for_like"})
        self.screenshot("before_like_click_personal_info_button")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button = self.wait_for_template(
            "点赞流程-个人信息按钮",
            "like_personal_info_button",
            timeout_seconds=self._fast_timeout(2.0, 0.8),
            threshold=0.78,
            region=(int(w * 0.12), int(h * 0.30), int(w * 0.48), int(h * 0.30)),
        )
        if not button:
            self.screenshot("like_personal_info_button_not_found")
            raise RuntimeError("Like flow could not find the personal info button.")

        point = Point(*button.center)
        self._record(
            {
                "type": "vision_feature",
                "feature": "like_personal_info_button",
                "source": "template",
                "x": button.x,
                "y": button.y,
                "width": button.width,
                "height": button.height,
                "score": round(button.score, 4),
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("点赞流程-点击个人信息", point, wait_seconds=self._fast_wait(2.0, 1.1))
        return self.screenshot("after_like_click_personal_info_button")

    def click_personal_home_view_button_for_like(self) -> Path:
        self._record({"type": "state", "state": "click_personal_home_view_button_for_like"})
        self.screenshot("before_like_click_personal_home_view_button")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button = self.wait_for_template(
            "点赞流程-个人主页点击查看按钮",
            "like_personal_home_view_button",
            timeout_seconds=self._fast_timeout(2.0, 0.8),
            threshold=0.76,
            region=(int(w * 0.16), int(h * 0.60), int(w * 0.36), int(h * 0.10)),
        )
        if not button:
            self.screenshot("like_personal_home_view_button_not_found")
            raise RuntimeError("Like flow could not find the personal home view button.")

        point = Point(*button.center)
        self._record(
            {
                "type": "vision_feature",
                "feature": "like_personal_home_view_button",
                "source": "template",
                "x": button.x,
                "y": button.y,
                "width": button.width,
                "height": button.height,
                "score": round(button.score, 4),
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("点赞流程-点击个人主页查看", point, wait_seconds=self._fast_wait(2.0, 1.1))
        return self.screenshot("after_like_click_personal_home_view_button")

    def detect_like_limit_toast_if_present(
        self,
        image: np.ndarray | None = None,
        *,
        timeout_seconds: float = 0.6,
    ) -> bool:
        self._record({"type": "state", "state": "detect_like_limit_toast_if_present"})
        deadline = time() + max(0.0, timeout_seconds)
        attempt = 0
        while True:
            attempt += 1
            current = image if attempt == 1 and image is not None else self.bot.screenshot_image()
            h, w = current.shape[:2]
            region = (0, int(h * 0.04), w, int(h * 0.30))
            toast = self._find_template_in_image(
                current,
                "like_limit_toast_text",
                threshold=0.70,
                region=region,
            )
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "like_limit_toast",
                    "present": toast is not None,
                    "attempt": attempt,
                    "x": toast.x if toast else None,
                    "y": toast.y if toast else None,
                    "width": toast.width if toast else None,
                    "height": toast.height if toast else None,
                    "score": round(toast.score, 4) if toast else 0.0,
                }
            )
            if toast:
                return True
            if time() >= deadline:
                return False
            self._sleep_with_watchdog(0.2, source="detect_like_limit_toast")

    def click_home_like_button_for_like(self, clicks: int = 5) -> Path:
        if clicks < 1:
            raise ValueError("Like click count must be at least 1.")

        self._record(
            {
                "type": "state",
                "state": "click_home_like_button_for_like",
                "clicks": clicks,
            }
        )
        self.screenshot("before_like_click_home_like_button")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button = self.wait_for_template(
            "点赞流程-右下角点赞按钮",
            "like_home_like_button",
            timeout_seconds=2.0,
            threshold=0.74,
            region=(int(w * 0.86), int(h * 0.78), int(w * 0.14), int(h * 0.10)),
        )
        if not button:
            self.screenshot("like_home_like_button_not_found")
            raise RuntimeError("Like flow could not find the lower-right like button.")

        point = Point(*button.center)
        self._record(
            {
                "type": "vision_feature",
                "feature": "like_home_like_button",
                "source": "template",
                "x": button.x,
                "y": button.y,
                "width": button.width,
                "height": button.height,
                "score": round(button.score, 4),
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        for index in range(clicks):
            self.tap(
                f"点赞流程-点击右下角点赞({index + 1}/{clicks})",
                point,
                wait_seconds=self._fast_wait(0.45, 0.25) if index + 1 < clicks else self._fast_wait(1.2, 0.65),
            )
        result = self.screenshot("after_like_click_home_like_button")
        checked_image = cv2.imread(str(result))
        self._last_like_limit_reached = self.detect_like_limit_toast_if_present(
            checked_image,
            timeout_seconds=self._fast_timeout(0.7, 0.25),
        )
        return result

    def click_home_back_button_for_like(self) -> Path:
        self._record({"type": "state", "state": "click_home_back_button_for_like"})
        self.screenshot("before_like_click_home_back_button")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button = self.wait_for_template(
            "点赞流程-个人主页返回按钮",
            "like_home_back_button",
            timeout_seconds=self._fast_timeout(2.0, 0.8),
            threshold=0.74,
            region=(0, int(h * 0.90), int(w * 0.30), int(h * 0.10)),
        )
        if not button:
            self.screenshot("like_home_back_button_not_found")
            raise RuntimeError("Like flow could not find the lower-left back button.")

        point = Point(*button.center)
        self._record(
            {
                "type": "vision_feature",
                "feature": "like_home_back_button",
                "source": "template",
                "x": button.x,
                "y": button.y,
                "width": button.width,
                "height": button.height,
                "score": round(button.score, 4),
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("点赞流程-点击个人主页返回", point, wait_seconds=self._fast_wait(1.5, 0.85))
        return self.screenshot("after_like_click_home_back_button")

    def click_friends_back_button_for_like(self) -> Path:
        self._record({"type": "state", "state": "click_friends_back_button_for_like"})
        self.screenshot("before_like_click_friends_back_button")

        image = self.bot.screenshot_image()
        h, w = image.shape[:2]
        button = self.wait_for_template(
            "点赞流程-好友列表返回按钮",
            "like_friends_back_button",
            timeout_seconds=self._fast_timeout(2.0, 0.8),
            threshold=0.74,
            region=(0, int(h * 0.90), int(w * 0.30), int(h * 0.10)),
        )
        if not button:
            self.screenshot("like_friends_back_button_not_found")
            raise RuntimeError("Like flow could not find the friend-list back button.")

        point = Point(*button.center)
        self._record(
            {
                "type": "vision_feature",
                "feature": "like_friends_back_button",
                "source": "template",
                "x": button.x,
                "y": button.y,
                "width": button.width,
                "height": button.height,
                "score": round(button.score, 4),
                "tap_x": point.x,
                "tap_y": point.y,
            }
        )
        self.tap("点赞流程-点击好友列表返回", point, wait_seconds=self._fast_wait(1.5, 0.85))
        return self.screenshot("after_like_click_friends_back_button")

    def complete_orange_card_effect_prompt(self) -> Path:
        skipped = self.skip_orange_card_effect_if_present(timeout_seconds=8.0)
        self._record(
            {
                "type": "state",
                "state": "orange_card_effect_prompt_done",
                "skipped": skipped,
            }
        )
        return self.screenshot("after_orange_card_effect_prompt")

    def complete_tongpao_feature_prompt(self) -> Path:
        self._record({"type": "state", "state": "complete_tongpao_feature_prompt"})
        self.close_signin_reward_if_present(timeout_seconds=0.8)
        self.screenshot("before_tongpao_feature_prompt")

        marker = self.wait_for_template(
            "同袍功能引导标识",
            "tongpao_feature_marker",
            timeout_seconds=1.2,
            threshold=0.72,
            region=(180, 1000, 430, 140),
        )
        if marker:
            self._record(
                {
                    "type": "vision_feature",
                    "feature": "tongpao_feature_marker",
                    "source": "template",
                    "x": marker.x,
                    "y": marker.y,
                    "width": marker.width,
                    "height": marker.height,
                    "score": round(marker.score, 4),
                }
            )

        alliance = self.wait_for_template(
            "同袍引导-同盟按钮",
            "alliance_button",
            timeout_seconds=1.2,
            threshold=0.72,
            region=(100, 1080, 190, 120),
        )
        if alliance:
            point = Point(*alliance.center)
            source = "template"
            score = round(alliance.score, 4)
        else:
            point = self.coords.portrait_alliance_button
            source = "fallback"
            score = 0.0

        self._record(
            {
                "type": "vision_feature",
                "feature": "alliance_button",
                "source": source,
                "x": point.x,
                "y": point.y,
                "score": score,
            }
        )
        self.tap("同袍引导-点击同盟", point, wait_seconds=1.5)
        self.close_signin_reward_if_present(timeout_seconds=1.2)
        return self.screenshot("after_click_alliance_from_tongpao_prompt")

    def select_latest_normal_s1(self, *, season1_taps: int = 2) -> None:
        self._record(
            {
                "type": "state",
                "state": "select_latest_normal_s1",
                "season1_taps": season1_taps,
            }
        )
        self.wait_for_template(
            "选服弹窗-赛季1标签",
            "season1_tab",
            timeout_seconds=1.0,
            threshold=0.78,
            region=(200, 970, 240, 120),
        )
        for index in range(max(1, season1_taps)):
            self.tap(
                f"选服弹窗-赛季1({index + 1})",
                self.coords.season1_tab,
                wait_seconds=self.quick_delay_seconds,
            )

        # The S1 list is transient in this game build: select the first row immediately.
        self.tap(
            "选服弹窗-普通赛季1最新服-左上第一服",
            self.coords.latest_s1_server,
            wait_seconds=self.quick_delay_seconds,
        )
        self.tap_server_selector_confirm("选服弹窗-确定", wait_seconds=1.0)
        self.screenshot("after_select_latest_s1")

    def enter_selected_server(self, *, wait_seconds: float = 5.0) -> None:
        self._record({"type": "state", "state": "enter_selected_server"})
        if self.click_recent_login_account_if_present(timeout_seconds=0.3):
            self.click_account_login_modal_if_present(timeout_seconds=2.0)
        self.click_template_or_point(
            "标题页-前往征战",
            "title_enter_button",
            self.coords.title_enter,
            timeout_seconds=3.0,
            threshold=0.78,
            region=(180, 940, 360, 130),
            wait_seconds=wait_seconds,
        )
        if self.click_recent_login_account_if_present(timeout_seconds=1.0):
            self.click_account_login_modal_if_present(timeout_seconds=2.0)
        self.wait_for_template(
            "服务器排队弹窗",
            "queue_title",
            timeout_seconds=1.5,
            threshold=0.82,
            region=(220, 450, 280, 120),
        )
        self.screenshot("after_enter_selected_server")

    def wait_with_screenshots(
        self,
        *,
        total_seconds: float,
        interval_seconds: float = 30.0,
        label: str = "wait",
    ) -> None:
        end_at = time() + max(0.0, total_seconds)
        index = 1
        while time() < end_at:
            remaining = end_at - time()
            self._sleep_with_watchdog(
                min(max(1.0, interval_seconds), max(0.0, remaining)),
                source=label,
            )
            self.screenshot(f"{label}_{index}")
            index += 1

    def continue_dialogs(
        self,
        *,
        taps: int,
        interval_seconds: float = 0.65,
        timeout_seconds: float = 0.8,
    ) -> Path:
        self._record(
            {
                "type": "state",
                "state": "continue_dialogs",
                "taps": taps,
                "interval_seconds": interval_seconds,
            }
        )
        self.screenshot("dialog_before_continue")
        for index in range(max(0, taps)):
            self.click_template_or_point(
                f"剧情对话-继续({index + 1})",
                "dialog_continue_icon",
                self.coords.dialog_continue,
                timeout_seconds=timeout_seconds,
                threshold=0.78,
                region=(580, 760, 140, 300),
                wait_seconds=interval_seconds,
            )
        self.screenshot("dialog_after_continue")
        self._record({"type": "state", "state": "continue_dialogs_done"})
        return self.record_path

    def continue_marker_dialog_until_blocked(
        self,
        *,
        marker_key: str,
        marker_label: str,
        continue_key: str = "dialog_continue_icon",
        fallback_continue: Point | None = None,
        max_taps: int = 30,
        interval_seconds: float = 0.65,
        marker_threshold: float = 0.78,
        continue_threshold: float = 0.78,
        marker_region: tuple[int, int, int, int] | None = None,
        continue_region: tuple[int, int, int, int] | None = None,
    ) -> Path:
        self._record(
            {
                "type": "state",
                "state": "continue_marker_dialog_until_blocked",
                "marker": marker_key,
                "continue": continue_key,
                "max_taps": max_taps,
            }
        )
        self.screenshot(f"{marker_label}_before_loop")
        for index in range(max(0, max_taps)):
            marker = self.bot.find_image(
                TEMPLATES[marker_key],
                threshold=marker_threshold,
                region=marker_region,
            )
            if not marker:
                self._record(
                    {
                        "type": "state",
                        "state": "marker_gone",
                        "marker": marker_key,
                        "after_taps": index,
                    }
                )
                break

            continue_icon = self.bot.find_image(
                TEMPLATES[continue_key],
                threshold=continue_threshold,
                region=continue_region,
            )
            if not continue_icon and fallback_continue is None:
                self._record(
                    {
                        "type": "state",
                        "state": "continue_icon_missing",
                        "marker": marker_key,
                        "after_taps": index,
                    }
                )
                break
            if not continue_icon:
                self._record(
                    {
                        "type": "state",
                        "state": "continue_icon_missing_use_fallback",
                        "marker": marker_key,
                        "after_taps": index,
                        "fallback_x": fallback_continue.x,
                        "fallback_y": fallback_continue.y,
                    }
                )

            self._record(
                {
                    "type": "match",
                    "label": marker_label,
                    "template": TEMPLATES[marker_key],
                    "x": marker.x,
                    "y": marker.y,
                    "width": marker.width,
                    "height": marker.height,
                    "score": round(marker.score, 4),
                }
            )
            self.tap(
                f"{marker_label}-继续({index + 1})",
                Point(*continue_icon.center) if continue_icon else fallback_continue,
                wait_seconds=interval_seconds,
            )
        else:
            self._record(
                {
                    "type": "state",
                    "state": "max_taps_reached",
                    "marker": marker_key,
                    "max_taps": max_taps,
                }
            )
        self.screenshot(f"{marker_label}_after_loop")
        return self.record_path

    def continue_old_man_until_blocked(
        self,
        *,
        max_taps: int = 30,
        interval_seconds: float = 0.65,
    ) -> Path:
        return self.continue_marker_dialog_until_blocked(
            marker_key="old_man_marker",
            marker_label="老者对话",
            continue_key="dialog_continue_icon",
            fallback_continue=self.coords.dialog_continue,
            max_taps=max_taps,
            interval_seconds=interval_seconds,
            continue_threshold=0.50,
            marker_region=(0, 180, 360, 520),
            continue_region=(580, 760, 140, 300),
        )

    def continue_scout_until_blocked(
        self,
        *,
        max_taps: int = 20,
        interval_seconds: float = 0.65,
    ) -> Path:
        return self.continue_marker_dialog_until_blocked(
            marker_key="scout_marker",
            marker_label="斥候对话",
            continue_key="landscape_dialog_continue_icon",
            fallback_continue=self.coords.landscape_dialog_continue,
            max_taps=max_taps,
            interval_seconds=interval_seconds,
            marker_region=(0, 80, 440, 560),
            continue_region=(1060, 490, 180, 160),
            continue_threshold=0.40,
        )

    def continue_zhuge_until_blocked(
        self,
        *,
        max_taps: int = 20,
        interval_seconds: float = 0.65,
    ) -> Path:
        return self.continue_marker_dialog_until_blocked(
            marker_key="zhuge_marker",
            marker_label="诸葛亮对话",
            continue_key="landscape_dialog_continue_icon",
            fallback_continue=self.coords.landscape_dialog_continue,
            max_taps=max_taps,
            interval_seconds=interval_seconds,
            marker_region=(0, 80, 450, 580),
            continue_region=(1060, 490, 180, 160),
            continue_threshold=0.40,
        )

    def old_man_choice_point(self, choice: int) -> Point:
        if choice == 1:
            return self.coords.old_man_choice_top
        if choice == 2:
            return self.coords.old_man_choice_middle
        if choice == 3:
            return self.coords.old_man_choice_bottom
        raise ValueError(f"Old-man quiz choice must be 1, 2, or 3: {choice}")

    def answer_old_man_quiz(
        self,
        *,
        choices: list[int],
        interval_seconds: float = 0.9,
        continue_after: bool = True,
    ) -> Path:
        self._record(
            {
                "type": "state",
                "state": "answer_old_man_quiz",
                "choices": choices,
            }
        )
        self.screenshot("old_man_quiz_before")
        for index, choice in enumerate(choices, start=1):
            point = self.old_man_choice_point(choice)
            self.tap(
                f"老者问答-{index}-选项{choice}",
                point,
                wait_seconds=interval_seconds,
            )
            self.screenshot(f"old_man_quiz_after_choice_{index}")
        if continue_after:
            self.continue_old_man_until_blocked(max_taps=12, interval_seconds=0.7)
        self._record({"type": "state", "state": "answer_old_man_quiz_done"})
        return self.record_path

    def confirm_avatar(self) -> Path:
        self._record({"type": "state", "state": "confirm_avatar"})
        self.click_template_or_point(
            "头像页-确定选择",
            "avatar_confirm_button",
            self.coords.avatar_confirm,
            timeout_seconds=3.0,
            threshold=0.78,
            region=(200, 1080, 330, 120),
            wait_seconds=1.0,
        )
        self.screenshot("after_avatar_confirm")
        return self.record_path

    def submit_random_name(self) -> Path:
        self._record({"type": "state", "state": "submit_random_name"})
        self.click_template_or_point(
            "起名页-进入乱世",
            "name_enter_button",
            self.coords.name_enter_world,
            timeout_seconds=3.0,
            threshold=0.78,
            region=(200, 1080, 330, 120),
            wait_seconds=2.0,
        )
        self.screenshot("after_name_submit")
        return self.record_path

    def select_xiliang_region(self) -> Path:
        self._record({"type": "state", "state": "select_xiliang_region"})
        self.wait_for_template(
            "落州页-选择起兵之地",
            "region_select_title",
            timeout_seconds=4.0,
            threshold=0.78,
            region=(200, 0, 330, 80),
        )
        self.screenshot("region_before_xiliang")
        self.tap("落州页-选择西凉区域", self.coords.xiliang_region, wait_seconds=1.0)
        self.click_template_or_point(
            "落州页-入驻西凉",
            "xiliang_enter_button",
            self.coords.xiliang_enter,
            timeout_seconds=3.0,
            threshold=0.78,
            region=(200, 1160, 330, 90),
            wait_seconds=1.0,
        )
        self.tap("落州确认弹窗-确认", self.coords.region_popup_confirm, wait_seconds=3.0)
        self.screenshot("after_xiliang_confirm")
        return self.record_path

    def tap_chapter_next(self) -> Path:
        self._record({"type": "state", "state": "tap_chapter_next"})
        self.click_template_or_point(
            "章节页-下一步",
            "chapter_next_button",
            self.coords.chapter_next,
            timeout_seconds=5.0,
            threshold=0.76,
            region=(1060, 620, 220, 100),
            wait_seconds=1.0,
        )
        self.screenshot("after_chapter_next")
        return self.record_path

    def tap_sequence(
        self,
        flow_node: str,
        steps: list[tuple[str, Point, float]],
        *,
        before: bool = True,
        after: bool = True,
    ) -> Path:
        self._record({"type": "flow_node", "node": flow_node, "step_count": len(steps)})
        if before:
            self.screenshot(f"{flow_node}_before")
        for label, point, wait_seconds in steps:
            self.tap(f"{flow_node}-{label}", point, wait_seconds=wait_seconds)
        if after:
            self.screenshot(f"{flow_node}_after")
        return self.record_path

    def confirm_resource_prompt(self) -> Path:
        return self.tap_sequence(
            "resource_prompt_confirm",
            [("资源包弹窗-确认", self.coords.resource_prompt_confirm, 1.0)],
        )

    def select_main_city_and_enter(self) -> Path:
        return self.tap_sequence(
            "main_city_enter",
            [
                ("选择主城-屏幕中心", self.coords.main_city_center, 0.5),
                ("主城浮层-入城", self.coords.main_city_enter, 1.0),
            ],
        )

    def recruit_free_twice(self) -> Path:
        return self.tap_sequence(
            "recruit_free_twice",
            [
                ("地图-招募", self.coords.recruit_button, 1.0),
                ("招募页-招募2次免费", self.coords.recruit_twice_free, 2.5),
                ("招募结果-继续", self.coords.recruit_result_continue, 0.8),
                ("招募页-返回", self.coords.city_back, 0.8),
                ("地图页-返回兜底", self.coords.map_back, 0.8),
            ],
        )

    def configure_initial_team(self) -> Path:
        return self.tap_sequence(
            "initial_team_config",
            [
                ("城内-部队一", self.coords.troop_one_card, 0.6),
                ("配置页-主将加号", self.coords.main_general_plus, 0.6),
                ("武将列表-第一行上阵", self.coords.general_list_first_up, 0.8),
                ("配置页-副将加号", self.coords.deputy_general_plus, 0.6),
                ("武将列表-第二行上阵", self.coords.general_list_second_up, 0.8),
                ("配置页-快速分兵", self.coords.quick_conscription, 0.6),
                ("分兵弹窗-确认", self.coords.conscription_confirm, 0.8),
                ("配置页-返回城内", self.coords.city_back, 0.8),
                ("城内-返回地图", self.coords.map_back, 1.0),
            ],
        )

    def occupy_first_land(self, *, wait_arrive_seconds: float = 12.0) -> Path:
        path = self.tap_sequence(
            "first_occupy_dispatch",
            [
                ("地图-第一块目标地", self.coords.first_land_target, 0.6),
                ("目标地-攻占", self.coords.occupy_button, 0.7),
                ("出征页-选择曹休队", self.coords.troop_card, 0.5),
                ("行军确认-确认", self.coords.march_confirm, 1.0),
            ],
        )
        self.wait_with_screenshots(
            total_seconds=wait_arrive_seconds,
            interval_seconds=wait_arrive_seconds,
            label="first_occupy_wait",
        )
        self.tap("首占奖励-点击领取", self.coords.first_reward, wait_seconds=0.8)
        self.screenshot("first_occupy_after_reward")
        return path

    def configure_spear_and_return(self) -> Path:
        return self.tap_sequence(
            "spear_config",
            [
                ("城内-部队一", self.coords.troop_one_card, 0.6),
                ("配置页-兵种选择", self.coords.troop_type_button, 0.6),
                ("兵种菜单-枪兵", self.coords.spear_type, 0.5),
                ("配置页-确认分兵", self.coords.split_confirm, 0.8),
                ("配置页-返回城内", self.coords.city_back, 0.8),
                ("城内-返回地图", self.coords.map_back, 1.0),
            ],
        )

    def support_ally_land(self, *, wait_arrive_seconds: float = 12.0) -> Path:
        path = self.tap_sequence(
            "support_ally_dispatch",
            [
                ("地图-支援目标地", self.coords.support_land_target, 0.6),
                ("目标地-行军", self.coords.march_button, 0.7),
                ("出征页-选择曹休队", self.coords.troop_card, 0.5),
                ("行军确认-确认", self.coords.march_confirm, 1.0),
            ],
        )
        self.wait_with_screenshots(
            total_seconds=wait_arrive_seconds,
            interval_seconds=wait_arrive_seconds,
            label="support_ally_wait",
        )
        self.tap("战斗页-跳过", self.coords.battle_skip, wait_seconds=2.0)
        self.tap("地图-回城", self.coords.recall_button, wait_seconds=1.0)
        self.screenshot("support_ally_after_recall")
        return path

    def reassign_main_after_support(self) -> Path:
        return self.tap_sequence(
            "reassign_main_after_support",
            [
                ("配置页-下阵曹休", self.coords.caoxiu_dismiss, 0.8),
                ("下阵弹窗-确认", self.coords.popup_confirm, 0.9),
                ("配置页-主将加号", self.coords.main_general_plus, 0.8),
                ("武将列表-第一行上阵", self.coords.general_list_first_up, 0.9),
            ],
        )

    def open_recruit_from_map(self) -> Path:
        return self.tap_sequence(
            "open_recruit_from_map",
            [
                ("地图-关闭土地面板兜底", self.coords.portrait_close_land_panel, 0.4),
                ("地图-招募", self.coords.portrait_map_recruit, 1.0),
            ],
        )

    def recruit_named_once(self) -> Path:
        self._record(
            {
                "type": "flow_node",
                "node": "recruit_named_once",
                "note": "Only tap the named-card pack before recruiting.",
            }
        )
        self.screenshot("recruit_named_once_before")
        self.tap("招募页-名将卡包", self.coords.portrait_named_pack, wait_seconds=0.5)
        self.tap("招募页-名将-招募1次免费", self.coords.portrait_named_recruit_once, wait_seconds=2.5)
        self.screenshot("recruit_named_once_result")
        self.tap(
            "招募结果-继续兜底",
            self.coords.portrait_recruit_result_continue,
            wait_seconds=0.8,
        )
        self.screenshot("recruit_named_once_after")
        return self.record_path

    def enter_main_city_portrait(self) -> Path:
        return self.tap_sequence(
            "enter_main_city_portrait",
            [
                ("地图-主城中心", self.coords.portrait_main_city, 0.6),
                ("主城浮层-入城兜底", self.coords.portrait_main_city_enter, 1.0),
            ],
        )

    def configure_second_team(self) -> Path:
        return self.tap_sequence(
            "configure_second_team",
            [
                ("城内-部队二", self.coords.portrait_second_team_card, 0.7),
                ("二队配置-主将加号", self.coords.portrait_main_general_plus, 0.7),
                ("武将列表-第一行上阵", self.coords.portrait_general_first_up, 0.8),
                ("二队配置-副将加号", self.coords.portrait_deputy_general_plus, 0.7),
                ("武将列表-第二行上阵", self.coords.portrait_general_second_up, 0.8),
                ("二队配置-快速分兵", self.coords.portrait_quick_conscription, 0.6),
                ("二队配置-确认分兵", self.coords.portrait_split_confirm, 0.8),
                ("二队配置-返回城内", self.coords.portrait_back, 0.8),
            ],
        )

    def probe_land(self, point: Point, *, label: str = "land") -> Path:
        self._record(
            {
                "type": "flow_node",
                "node": "probe_land",
                "x": point.x,
                "y": point.y,
            }
        )
        self.tap(f"探地-{label}", point, wait_seconds=0.8)
        self.screenshot(f"probe_land_{label}_{point.x}_{point.y}")
        return self.record_path

    def farm_land(self, point: Point, *, team: int, wait_arrive_seconds: float = 12.0) -> Path:
        if team not in {1, 2}:
            raise ValueError(f"Farm team must be 1 or 2: {team}")
        self._record(
            {
                "type": "flow_node",
                "node": "farm_land",
                "x": point.x,
                "y": point.y,
                "team": team,
                "rule": "team1_empty_only; team2_level_1_2_3",
            }
        )
        self.screenshot(f"farm_land_before_team{team}_{point.x}_{point.y}")
        self.tap(f"打地-选择土地-team{team}", point, wait_seconds=0.6)
        self.tap(f"打地-攻占-team{team}", self.coords.portrait_land_occupy, wait_seconds=0.8)
        self.tap(f"出征页-选择队伍{team}", self._portrait_troop_card(team), wait_seconds=0.6)
        self.tap(f"出征页-确认-team{team}", self.coords.march_confirm, wait_seconds=1.0)
        self.wait_with_screenshots(
            total_seconds=wait_arrive_seconds,
            interval_seconds=wait_arrive_seconds,
            label=f"farm_land_team{team}_wait",
        )
        self.screenshot(f"farm_land_after_team{team}_{point.x}_{point.y}")
        return self.record_path

    @staticmethod
    def _portrait_troop_card(team: int) -> Point:
        if team == 1:
            return Point(360, 940)
        if team == 2:
            return Point(360, 1040)
        raise ValueError(f"Unsupported team: {team}")

    def run_flow_node(self, node: str) -> Path:
        if node == "select_last_server_role_only":
            return self.select_last_role_in_server_selector()
        if node == "select_last_server_entry":
            return self.select_last_entry_in_server_selector()
        if node == "confirm_selected_server_entry":
            return self.confirm_selected_server_entry_and_enter()
        if node == "signin_reward_prompt":
            return self.complete_signin_reward_prompt()
        if node == "enter_world_again_prompt":
            self.click_enter_world_again_if_present(timeout_seconds=2.0)
            return self.screenshot("after_enter_world_again_prompt")
        if node == "same_server_select_last_role":
            self.select_last_same_server_role_if_present()
            return self.screenshot("after_same_server_select_last_role_node")
        if node == "region_default_select_prompt":
            self.select_default_region_if_present(timeout_seconds=2.0)
            return self.screenshot("after_region_default_select_prompt")
        if node == "inactive_reselect_region_prompt":
            self.handle_entry_preconditions(max_rounds=8)
            return self.screenshot("after_inactive_reselect_region_prompt")
        if node == "military_council_back_prompt":
            self.close_military_council_if_present(timeout_seconds=2.0)
            return self.screenshot("after_military_council_back_prompt")
        if node == "exit_confirm_prompt":
            self.close_exit_confirm_if_present(timeout_seconds=2.0)
            return self.screenshot("after_exit_confirm_prompt")
        if node == "recover_to_main_screen":
            self.recover_to_main_screen(max_steps=6)
            return self.screenshot("after_recover_to_main_screen_node")
        if node == "orange_card_effect_prompt":
            return self.complete_orange_card_effect_prompt()
        if node == "click_other_area_return_hint":
            return self.complete_click_other_area_return_hint()
        if node == "alliance_back_to_main":
            return self.back_to_main_from_alliance()
        if node == "like_open_friends_list":
            return self.open_friends_list_for_like()
        if node == "like_click_dabai_friend_button":
            return self.click_dabai_friend_button_for_like()
        if node == "like_add_missing_dabai_friend":
            self.request_missing_like_friend()
            return self.click_friends_back_button_for_like()
        if node == "like_click_personal_info_button":
            return self.click_personal_info_button_for_like()
        if node == "like_click_personal_home_view_button":
            return self.click_personal_home_view_button_for_like()
        if node == "like_click_home_like_button":
            return self.click_home_like_button_for_like()
        if node == "like_click_home_back_button":
            return self.click_home_back_button_for_like()
        if node == "like_click_friends_back_button":
            return self.click_friends_back_button_for_like()
        if node == "gacha_open_recruit_if_red_dot":
            return self.open_recruit_if_red_dot_for_gacha()
        if node == "gacha_select_named_pack":
            return self.select_named_pack_for_gacha()
        if node == "gacha_click_free_recruit_once":
            return self.click_free_recruit_once_for_gacha()
        if node == "gacha_click_half_recruit_once":
            return self.click_half_recruit_once_for_gacha_if_available()
        if node == "gacha_back_from_recruit_result":
            return self.back_from_recruit_result_for_gacha()
        if node == "gacha_back_from_recruit_page":
            return self.back_from_recruit_page_for_gacha()
        if node == "gacha_free_and_half":
            self.run_free_gacha_if_available()
            return self.screenshot("after_gacha_free_and_half_node")
        if node == "gamecircle_signin":
            return self.run_gamecircle_signin()
        if node == "account_switch_to_role_select":
            return self.switch_account_to_role_select()
        if node == "account_login_and_select_last_role":
            return self.login_current_account_and_select_last_role()
        if node == "daily_signin_like_gacha":
            return self.run_daily_signin_like_gacha()
        if node == "account_role_daily_cycle":
            max_cycles = int(os.environ.get("SGZZ_DAILY_CYCLE_LIMIT", "3"))
            return self.run_account_role_daily_cycle(max_cycles=max_cycles)
        if node == "account_remaining_roles_daily_cycle":
            max_cycles = int(os.environ.get("SGZZ_REMAINING_ROLE_CYCLE_LIMIT", "20"))
            return self.run_account_remaining_roles_daily_cycle(max_cycles=max_cycles)
        if node == "account_batch_remaining_roles_daily_cycle":
            max_cycles = int(os.environ.get("SGZZ_REMAINING_ROLE_CYCLE_LIMIT", "20"))
            accounts_file = os.environ.get("SGZZ_ACCOUNTS_FILE", "").strip() or None
            return self.run_account_batch_remaining_roles_daily_cycle(
                accounts_file=accounts_file,
                max_cycles_per_account=max_cycles,
            )
        if node == "main_known_retreat_prompt":
            return self.complete_known_retreat_prompt()
        if node == "tongpao_feature_prompt":
            return self.complete_tongpao_feature_prompt()
        if node == "resource_prompt_confirm":
            return self.confirm_resource_prompt()
        if node == "main_city_enter":
            return self.select_main_city_and_enter()
        if node == "recruit_free_twice":
            return self.recruit_free_twice()
        if node == "initial_team_config":
            return self.configure_initial_team()
        if node == "first_occupy":
            return self.occupy_first_land()
        if node == "spear_config":
            return self.configure_spear_and_return()
        if node == "support_ally":
            return self.support_ally_land()
        if node == "reassign_main_after_support":
            return self.reassign_main_after_support()
        if node == "open_recruit_from_map":
            return self.open_recruit_from_map()
        if node == "recruit_named_once":
            return self.recruit_named_once()
        if node == "enter_main_city_portrait":
            return self.enter_main_city_portrait()
        if node == "configure_second_team":
            return self.configure_second_team()
        raise ValueError(f"Unknown SGZZ flow node: {node}")

    def select_and_enter_latest_s1(
        self,
        *,
        launch: bool = True,
        launch_wait_seconds: float = 8.0,
        cancel_restore: bool = True,
        season1_taps: int = 2,
        enter: bool = True,
        enter_wait_seconds: float = 5.0,
        queue_wait_seconds: float = 0.0,
        queue_poll_seconds: float = 30.0,
    ) -> Path:
        self._record({"type": "state", "state": "start"})
        if launch:
            self.launch(wait_seconds=launch_wait_seconds)
        if cancel_restore:
            self.dismiss_restore_prompt()
        self.open_server_selector()
        self.select_latest_normal_s1(season1_taps=season1_taps)
        if enter:
            self.enter_selected_server(wait_seconds=enter_wait_seconds)
        if queue_wait_seconds > 0:
            self.wait_with_screenshots(
                total_seconds=queue_wait_seconds,
                interval_seconds=queue_poll_seconds,
                label="queue",
            )
        self._record({"type": "state", "state": "done"})
        return self.record_path
