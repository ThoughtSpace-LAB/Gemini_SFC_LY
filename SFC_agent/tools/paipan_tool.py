# todo list 本卦六神有问题排训有问题

import datetime
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from lunarcalendar import Converter, Solar, Lunar
import datetime
from google.adk.tools import ToolContext

# ==========================================
# 第一部分：基础数据定义 (Enums & Constants)
# ==========================================

class YinYang(Enum):
    YIN = 0
    YANG = 1

class YaoStatus(Enum):
    STATIC = 0  # 静爻
    MOVING = 1  # 动爻

class Element(Enum):
    METAL = "金"
    WOOD = "木"
    WATER = "水"
    FIRE = "火"
    EARTH = "土"

class TrigramType(Enum):
    # 按照 PDF 顺序对应数字 1-8
    QIAN = (1, "乾", "天", Element.METAL, [1, 1, 1])  # 三连
    KUN  = (2, "坤", "地", Element.EARTH, [0, 0, 0])  # 六断
    ZHEN = (3, "震", "雷", Element.WOOD,  [1, 0, 0])  # 仰盂 (初爻为阳)
    XUN  = (4, "巽", "风", Element.WOOD,  [0, 1, 1])  # 下断 (初爻为阴)
    KAN  = (5, "坎", "水", Element.WATER, [0, 1, 0])  # 中满
    LI   = (6, "离", "火", Element.FIRE,  [1, 0, 1])  # 中虚
    GEN  = (7, "艮", "山", Element.EARTH, [0, 0, 1])  # 覆碗 (上爻为阳)
    DUI  = (8, "兑", "泽", Element.METAL, [1, 1, 0])  # 上缺 (上爻为阴)

    def __init__(self, number, name, symbol, element, lines):
        self.number = number
        self.chn_name = name
        self.symbol = symbol
        self.element = element
        self.lines = lines # [初, 二, 三] 0为阴 1为阳

    @classmethod
    def from_number(cls, num):
        # 1-8, 0 treated as 8 based on PDF logic (mod 8)
        if num == 0: num = 8
        for t in cls:
            if t.number == num:
                return t
        raise ValueError(f"Invalid Trigram Number: {num}")

class Stem(Enum):
    JIA = (1, "甲", Element.WOOD)
    YI  = (2, "乙", Element.WOOD)
    BING= (3, "丙", Element.FIRE)
    DING= (4, "丁", Element.FIRE)
    WU  = (5, "戊", Element.EARTH)
    JI  = (6, "己", Element.EARTH)
    GENG= (7, "庚", Element.METAL)
    XIN = (8, "辛", Element.METAL)
    REN = (9, "壬", Element.WATER)
    GUI = (10,"癸", Element.WATER)

    def __init__(self, num, name, element):
        self.number = num
        self.chn_name = name
        self.element = element

class Branch(Enum):
    ZI   = (1,  "子", Element.WATER)
    CHOU = (2,  "丑", Element.EARTH)
    YIN  = (3,  "寅", Element.WOOD)
    MAO  = (4,  "卯", Element.WOOD)
    CHEN = (5,  "辰", Element.EARTH)
    SI   = (6,  "巳", Element.FIRE)
    WU   = (7,  "午", Element.FIRE)
    WEI  = (8,  "未", Element.EARTH)
    SHEN = (9,  "申", Element.METAL)
    YOU  = (10, "酉", Element.METAL)
    XU   = (11, "戌", Element.EARTH)
    HAI  = (12, "亥", Element.WATER)

    def __init__(self, num, name, element):
        self.number = num
        self.chn_name = name
        self.element = element

    @classmethod
    def from_number(cls, num):
        # Handle mod 12 result where 0 -> 12
        if num == 0: num = 12
        for b in cls:
            if b.number == num:
                return b
        raise ValueError(f"Invalid Branch Number: {num}")

class SixRelative(Enum):
    BROTHER = "兄弟"
    CHILD   = "子孙"
    WEALTH  = "妻财"
    OFFICIAL= "官鬼"
    PARENT  = "父母"

class SixGod(Enum):
    QING_LONG = "青龙"
    ZHU_QUE   = "朱雀"
    GOU_CHEN  = "勾陈"
    TENG_SHE  = "腾蛇"
    BAI_HU    = "白虎"
    XUAN_WU   = "玄武"

# ==========================================
# 第二部分：数据结构 (Data Structures)
# ==========================================

@dataclass
class Yao:
    """代表卦中的一个'爻'"""
    position: int      # 1-6 (初爻到上爻)
    yin_yang: YinYang
    status: YaoStatus  # 动爻还是静爻
    
    # 后续计算属性
    stem: Optional[Stem] = None
    branch: Optional[Branch] = None
    relative: Optional[SixRelative] = None
    god: Optional[SixGod] = None
    
    # 伏神信息 (如果本位是飞神)
    hidden_relative: Optional[SixRelative] = None
    hidden_branch: Optional[Branch] = None
    hidden_stem: Optional[Stem] = None

    @property
    def name(self):
        prefix = "九" if self.yin_yang == YinYang.YANG else "六"
        pos_map = {1: "初", 2: "二", 3: "三", 4: "四", 5: "五", 6: "上"}
        return f"{pos_map[self.position]}{prefix}" if self.position not in [1,6] else f"{prefix}{pos_map[self.position]}"

    @property
    def symbol_char(self):
        if self.status == YaoStatus.MOVING:
            return "O" if self.yin_yang == YinYang.YANG else "X"
        return "▅▅▅▅▅" if self.yin_yang == YinYang.YANG else "▅▅　▅▅"

@dataclass
class Hexagram:
    """代表一个'卦' (本卦或变卦)"""
    lines: List[Yao]  # 0为初爻，5为上爻
    upper_trigram: TrigramType
    lower_trigram: TrigramType
    is_changed_hexagram: bool = False
    
    # 后续计算属性
    palace: Optional[TrigramType] = None  # 所属宫
    shi_index: int = -1  # 世爻索引 (0-5)
    ying_index: int = -1 # 应爻索引 (0-5)

    @property
    def full_name(self):
        return f"{self.upper_trigram.chn_name}{self.lower_trigram.chn_name}"

# ==========================================
# 第三部分：核心逻辑引擎 (Logic Engine)
# ==========================================

class LiuYaoEngine:
    
    # 纳甲规则表 (PDF Page 7-8)
    # 格式: (内卦起始支, 内卦方向, 外卦起始支, 外卦方向, 干)
    # 方向: 1 顺行, -1 逆行
    NAJIA_RULES = {
        TrigramType.QIAN: (Branch.ZI, 1, Branch.WU, 1, Stem.JIA, Stem.REN), # 乾内甲子外壬午
        TrigramType.KAN:  (Branch.YIN, 1, Branch.SHEN, 1, Stem.WU, Stem.WU), # 坎内戊寅外戊申
        TrigramType.GEN:  (Branch.CHEN, 1, Branch.XU, 1, Stem.BING, Stem.BING), # 艮内丙辰外丙戌
        TrigramType.ZHEN: (Branch.ZI, 1, Branch.WU, 1, Stem.GENG, Stem.GENG), # 震内庚子外庚午
        
        TrigramType.KUN:  (Branch.WEI, -1, Branch.CHOU, -1, Stem.YI, Stem.GUI), # 坤内乙未外癸丑
        TrigramType.XUN:  (Branch.CHOU, -1, Branch.WEI, -1, Stem.XIN, Stem.XIN), # 巽内辛丑外辛未
        TrigramType.LI:   (Branch.MAO, -1, Branch.YOU, -1, Stem.JI, Stem.JI),   # 离内己卯外己酉
        TrigramType.DUI:  (Branch.SI, -1, Branch.HAI, -1, Stem.DING, Stem.DING) # 兑内丁巳外丁亥
    }

    @staticmethod
    def get_trigram_from_lines(lines_3: List[Yao]) -> TrigramType:
        """根据3个爻(初到上)确定八卦"""
        vals = [1 if l.yin_yang == YinYang.YANG else 0 for l in lines_3]
        # vals is [bottom, mid, top]
        for t in TrigramType:
            if t.lines == vals:
                return t
        return TrigramType.QIAN # Fallback

    @staticmethod
    def create_hexagram_from_numbers(upper_num: int, lower_num: int, moving_line_idx: int = -1) -> Tuple[Hexagram, Hexagram]:
        """
        根据数字起卦 (PDF 1.1, 1.2)
        moving_line_idx: 1-6, if -1 no moving (unlikely in this logic)
        """
        upper = TrigramType.from_number(upper_num)
        lower = TrigramType.from_number(lower_num)
        
        # 构建本卦爻
        main_lines = []
        # 下卦 (1,2,3)
        for i in range(3):
            yy = YinYang.YANG if lower.lines[i] == 1 else YinYang.YIN
            # Check moving
            status = YaoStatus.MOVING if (i + 1) == moving_line_idx else YaoStatus.STATIC
            main_lines.append(Yao(i+1, yy, status))
            
        # 上卦 (4,5,6)
        for i in range(3):
            yy = YinYang.YANG if upper.lines[i] == 1 else YinYang.YIN
            status = YaoStatus.MOVING if (i + 4) == moving_line_idx else YaoStatus.STATIC
            main_lines.append(Yao(i+4, yy, status))
            
        main_gua = Hexagram(main_lines, upper, lower, False)
        
        # 构建变卦 (PDF: 动爻变，其余不变)
        changed_lines = []
        for line in main_lines:
            new_yy = line.yin_yang
            if line.status == YaoStatus.MOVING:
                new_yy = YinYang.YIN if line.yin_yang == YinYang.YANG else YinYang.YANG
            changed_lines.append(Yao(line.position, new_yy, YaoStatus.STATIC))
            
        # 重新计算变卦的上下卦
        c_lower = LiuYaoEngine.get_trigram_from_lines(changed_lines[0:3])
        c_upper = LiuYaoEngine.get_trigram_from_lines(changed_lines[3:6])
        
        changed_gua = Hexagram(changed_lines, c_upper, c_lower, True)
        
        return main_gua, changed_gua

    @staticmethod
    def method_date(year_b: int, month: int, day: int, hour_b: int) -> Tuple[Hexagram, Hexagram]:
        """
        PDF 1.1: 当前日期排卦版
        (年支+月+日)/8 = 上卦
        (年支+月+日+时支)/8 = 下卦
        (年支+月+日+时支)/6 = 动爻
        """
        sum_upper = year_b + month + day
        sum_total = sum_upper + hour_b
        
        upper_num = sum_upper % 8
        if upper_num == 0: upper_num = 8
        
        lower_num = sum_total % 8
        if lower_num == 0: lower_num = 8
        
        moving_num = sum_total % 6
        if moving_num == 0: moving_num = 6
        
        return LiuYaoEngine.create_hexagram_from_numbers(upper_num, lower_num, moving_num)

    @staticmethod
    def method_coins(coins_results: List[int]) -> Tuple[Hexagram, Hexagram]:
        """
        PDF 1.3: 钱币排卦版
        coins_results: list of 6 ints, representing number of 'Zheng' (Heads/Pattern side)
        from bottom (1st) to top (6th).
        PDF Rules (Page 5):
        3正 -> 老阴 (X) -> 变阳
        2正 -> 少阳 (Static)
        1正 -> 少阴 (Static)
        0正 -> 老阳 (O) -> 变阴
        """
        if len(coins_results) != 6:
            raise ValueError("Need exactly 6 coin toss results")
            
        main_lines = []
        
        for i, zheng_count in enumerate(coins_results):
            pos = i + 1
            if zheng_count == 3:
                # 老阴，动，本卦为阴
                main_lines.append(Yao(pos, YinYang.YIN, YaoStatus.MOVING))
            elif zheng_count == 2:
                # 少阳，静，本卦为阳 (PDF: 2正-少阳)
                main_lines.append(Yao(pos, YinYang.YANG, YaoStatus.STATIC))
            elif zheng_count == 1:
                # 少阴，静，本卦为阴 (PDF: 1正-少阴)
                main_lines.append(Yao(pos, YinYang.YIN, YaoStatus.STATIC))
            elif zheng_count == 0:
                # 老阳，动，本卦为阳
                main_lines.append(Yao(pos, YinYang.YANG, YaoStatus.MOVING))
            else:
                raise ValueError(f"Invalid coin count: {zheng_count}")

        # Determine Trigrams
        lower = LiuYaoEngine.get_trigram_from_lines(main_lines[0:3])
        upper = LiuYaoEngine.get_trigram_from_lines(main_lines[3:6])
        main_gua = Hexagram(main_lines, upper, lower, False)

        # Build Changed Hexagram
        changed_lines = []
        for line in main_lines:
            new_yy = line.yin_yang
            if line.status == YaoStatus.MOVING:
                new_yy = YinYang.YIN if line.yin_yang == YinYang.YANG else YinYang.YANG
            changed_lines.append(Yao(line.position, new_yy, YaoStatus.STATIC))
            
        c_lower = LiuYaoEngine.get_trigram_from_lines(changed_lines[0:3])
        c_upper = LiuYaoEngine.get_trigram_from_lines(changed_lines[3:6])
        changed_gua = Hexagram(changed_lines, c_upper, c_lower, True)

        return main_gua, changed_gua

    @staticmethod
    def calculate_shi_ying(gua: Hexagram):
        """
        PDF 2: 寻世爻、应爻
        口诀: 天同二世天异五, 地同四世地异初; 本宫六世三世异, 人同游魂人变归
        """
        # Get binary representation lines (0/1)
        # Upper (Heaven=2, Man=1, Earth=0 relative to trigram)
        # Lower (Heaven=2, Man=1, Earth=0 relative to trigram)
        
        up = gua.upper_trigram.lines # [bot, mid, top] i.e. [earth, man, heaven]
        lo = gua.lower_trigram.lines 
        
        earth_same = up[0] == lo[0]
        man_same   = up[1] == lo[1]
        heaven_same= up[2] == lo[2]
        
        shi = 0
        
        # 纯卦 (八纯) - 本宫六世 (All same)
        if gua.upper_trigram == gua.lower_trigram:
            shi = 6
        # 三世异 (All different) - PDF: 外卦内卦完全不同 -> 三世
        elif (not earth_same) and (not man_same) and (not heaven_same):
            shi = 3
        # 天同二世: 只有天爻相同 (Means Man and Earth are different)
        elif heaven_same and (not man_same) and (not earth_same):
            shi = 2
        # 天异五: 只有天爻不同 (Means Man and Earth are same)
        elif (not heaven_same) and man_same and earth_same:
            shi = 5
        # 地同四世: 只有地爻相同
        elif earth_same and (not man_same) and (not heaven_same):
            shi = 4
        # 地异初: 只有地爻不同
        elif (not earth_same) and man_same and heaven_same:
            shi = 1
        # 人同游魂 (游魂于四): 只有人爻相同
        elif man_same and (not heaven_same) and (not earth_same):
            shi = 4 # 游魂卦
        # 人变归 (归于三): 只有人爻不同
        elif (not man_same) and heaven_same and earth_same:
            shi = 3 # 归魂卦
            
        gua.shi_index = shi - 1 # 0-based index
        # 应爻永远隔两位
        # 1->4, 2->5, 3->6, 4->1, 5->2, 6->3
        gua.ying_index = (gua.shi_index + 3) % 6

    @staticmethod
    def calculate_palace(gua: Hexagram):
        """
        PDF 3: 寻卦宫
        口诀: 世在内卦外卦为卦宫。世在外卦内卦全变为卦宫。归魂内卦为卦宫。
        """
        shi_pos = gua.shi_index + 1 # 1-6
        
        # 1. 内外一致 -> 本身 (Logic handled by 'Shi in Outer' logic usually, but strict check first)
        if gua.upper_trigram == gua.lower_trigram:
            gua.palace = gua.upper_trigram
            return

        # 2. 归魂卦特殊处理 (通常是三世，且原本是人变归)
        # PDF Definition: "如果五爻变后内外卦一致，则为归魂卦，归魂内卦为卦宫"
        # 这是一个验证方法。简单法：世爻在3爻，且不是"三世异"（全不同）。
        # Check standard logic first:
        
        is_gui_hun = False
        # Man different, Heaven/Earth same -> Guihun (Shi at 3)
        up = gua.upper_trigram.lines
        lo = gua.lower_trigram.lines
        if (up[2] == lo[2]) and (up[0] == lo[0]) and (up[1] != lo[1]):
             is_gui_hun = True

        if is_gui_hun:
             gua.palace = gua.lower_trigram
             return

        # 3. 世在内卦 (1, 2, 3) -> 外卦为宫
        if shi_pos <= 3:
            gua.palace = gua.upper_trigram
            return
            
        # 4. 世在外卦 (4, 5, 6) -> 内卦全变为宫
        if shi_pos >= 4:
            # 内卦全变 (0->1, 1->0)
            inverted_lines_vals = [1 if x==0 else 0 for x in gua.lower_trigram.lines]
            # Find trigram with these lines
            for t in TrigramType:
                if t.lines == inverted_lines_vals:
                    gua.palace = t
                    return
        
        # Fallback (Should not reach here if logic covers all)
        gua.palace = gua.upper_trigram 

    @staticmethod
    def calculate_najia_and_relatives(gua: Hexagram, palace: TrigramType, day_stem: Optional[Stem] = None):
        """
        PDF 4 & 5: 纳甲、定六亲
        """
        palace_element = palace.element
        
        def assign_lines(trigram: TrigramType, start_index: int):
            rule = LiuYaoEngine.NAJIA_RULES[trigram]
            # rule: (start_branch, direction, ..., stem)
            # Inner: rule[0], rule[1], rule[4] (Stem for inner/outer often same except Qian)
            # Outer: rule[2], rule[3], rule[5]
            
            is_inner = (start_index == 0)
            start_branch = rule[0] if is_inner else rule[2]
            direction = rule[1] if is_inner else rule[3]
            stem = rule[4] if is_inner else rule[5] # rule[5] for Qian outer is Ren
            
            curr_branch_num = start_branch.number
            
            for i in range(3):
                idx = start_index + i
                
                # Assign Stem/Branch
                b = Branch.from_number(curr_branch_num)
                gua.lines[idx].branch = b
                gua.lines[idx].stem = stem
                
                # Calculate Relative (Six Kin)
                # Relation of Line Element TO Palace Element
                line_el = b.element
                
                # Logic PDF Page 8-9
                # Same = Brother
                # Line 生 Palace = Parent (Wait, PDF says "土为父母" for "火" palace? No)
                # PDF Example Page 9: Palace Gen (Earth).
                # Line Mao (Wood) -> Wood conquers Earth -> Official (官鬼). Correct.
                # Line Si (Fire) -> Fire births Earth -> Parent (父母). Correct.
                # Line Wei (Earth) -> Earth same Earth -> Brother (兄弟). Correct.
                # Line Zi (Water) -> Earth conquers Water -> Wealth (妻财). Correct.
                # Line Shen (Metal) -> Earth births Metal -> Child (子孙). Correct.
                
                rel = None
                if line_el == palace_element:
                    rel = SixRelative.BROTHER
                elif LiuYaoEngine.is_births(line_el, palace_element): # Line births Palace
                    rel = SixRelative.PARENT
                elif LiuYaoEngine.is_conquers(line_el, palace_element): # Line conquers Palace
                    rel = SixRelative.OFFICIAL
                elif LiuYaoEngine.is_births(palace_element, line_el): # Palace births Line
                    rel = SixRelative.CHILD
                elif LiuYaoEngine.is_conquers(palace_element, line_el): # Palace conquers Line
                    rel = SixRelative.WEALTH
                
                gua.lines[idx].relative = rel
                
                # Move to next branch
                curr_branch_num += (direction * 2) # Skips one branch (Zi -> Yin -> Chen)
                # Handle wrap around (1-12 cycle)
                curr_branch_num = ((curr_branch_num - 1) % 12) + 1
                
        # Inner Trigram (Lines 0-2)
        assign_lines(gua.lower_trigram, 0)
        # Outer Trigram (Lines 3-5)
        assign_lines(gua.upper_trigram, 3)
        
        # 伏神 logic (PDF Page 9)
        # Check if all 5 relatives exist
        existing_rels = set(l.relative for l in gua.lines)
        all_rels = set(SixRelative)
        missing_rels = all_rels - existing_rels
        
        if missing_rels and not gua.is_changed_hexagram:
            # Construct Pure Hexagram of the Palace
            # Palace is the Gua. e.g. Gen Palace -> Gen upper, Gen lower
            pure_lines = []
            # We don't need full Hexagram obj, just need to run Najia logic on the Palace Trigram
            # Simulating lines for logic reuse
            temp_gua = Hexagram(
                [Yao(i+1, YinYang.YANG, YaoStatus.STATIC) for i in range(6)], # Dummy lines
                palace, palace
            )
            LiuYaoEngine.calculate_najia_and_relatives(temp_gua, palace) # Recursive but depth 1
            
            # Find the missing relative in the Pure Hexagram
            for missing in missing_rels:
                # Find which line in Pure Hexagram has this relative
                found_yao = next((y for y in temp_gua.lines if y.relative == missing), None)
                if found_yao:
                    # Map to Main Hexagram line
                    # Usually mapped by index.
                    target_line = gua.lines[found_yao.position - 1]
                    target_line.hidden_relative = found_yao.relative
                    target_line.hidden_branch = found_yao.branch
                    target_line.hidden_stem = found_yao.stem

    @staticmethod
    def calculate_six_gods(gua: Hexagram, day_stem: Stem):
        """
        PDF 6: 定六神
        """
        # Mapping Starting God based on Day Stem
        # 甲乙 -> 青龙
        # 丙丁 -> 朱雀
        # 戊   -> 勾陈
        # 己   -> 腾蛇
        # 庚辛 -> 白虎
        # 壬癸 -> 玄武
        
        god_order = [
            SixGod.QING_LONG, SixGod.ZHU_QUE, SixGod.GOU_CHEN,
            SixGod.TENG_SHE, SixGod.BAI_HU, SixGod.XUAN_WU
        ]
        
        start_idx = 0
        if day_stem in [Stem.JIA, Stem.YI]: start_idx = 0
        elif day_stem in [Stem.BING, Stem.DING]: start_idx = 1
        elif day_stem == Stem.WU: start_idx = 2
        elif day_stem == Stem.JI: start_idx = 3
        elif day_stem in [Stem.GENG, Stem.XIN]: start_idx = 4
        elif day_stem in [Stem.REN, Stem.GUI]: start_idx = 5
        
        for i in range(6):
            god = god_order[(start_idx + i) % 6]
            gua.lines[i].god = god

    @staticmethod
    def is_births(source: Element, target: Element) -> bool:
        # 水生木，木生火，火生土，土生金，金生水
        pairs = {
            Element.WATER: Element.WOOD,
            Element.WOOD: Element.FIRE,
            Element.FIRE: Element.EARTH,
            Element.EARTH: Element.METAL,
            Element.METAL: Element.WATER
        }
        return pairs.get(source) == target

    @staticmethod
    def is_conquers(source: Element, target: Element) -> bool:
        # 水克火，火克金，金克木，木克土，土克水
        pairs = {
            Element.WATER: Element.FIRE,
            Element.FIRE: Element.METAL,
            Element.METAL: Element.WOOD,
            Element.WOOD: Element.EARTH,
            Element.EARTH: Element.WATER
        }
        return pairs.get(source) == target

# ==========================================
# 第四部分：用户接口与显示 (UI & Main)
# ==========================================

class LiuYaoSystem:
    def __init__(self):
        # 天干地支查找表
        self.STEMS = [Stem.JIA, Stem.YI, Stem.BING, Stem.DING, Stem.WU, 
                      Stem.JI, Stem.GENG, Stem.XIN, Stem.REN, Stem.GUI]
        self.BRANCHES = [Branch.ZI, Branch.CHOU, Branch.YIN, Branch.MAO, 
                         Branch.CHEN, Branch.SI, Branch.WU, Branch.WEI,
                         Branch.SHEN, Branch.YOU, Branch.XU, Branch.HAI]
    
    def solar_to_ganzhi(self, solar_date: datetime.datetime) -> Dict:
        """
        将阳历日期转换为农历和干支信息
        
        Returns:
            dict with keys: lunar_year, lunar_month, lunar_day, 
                          year_branch_num, month_branch_num, day_stem_num, 
                          hour_branch_num, year_stem, year_branch
        """
        # 转换为农历
        solar = Solar(solar_date.year, solar_date.month, solar_date.day)
        lunar = Converter.Solar2Lunar(solar)
        
        # 计算时辰地支（23-1点为子时=1）
        hour = solar_date.hour
        hour_branch_idx = ((hour + 1) // 2) % 12
        hour_branch_num = hour_branch_idx + 1 if hour_branch_idx != 11 else 12
        
        # 使用lunarcalendar库获取干支信息
        # 年份天干地支（从1900年庚子年开始计算）
        year_offset = solar_date.year - 1900  # 1900年是庚子年
        year_stem_idx = (year_offset + 6) % 10  # 1900年天干是庚(7)，索引6
        year_branch_idx = year_offset % 12  # 1900年地支是子(1)，索引0
        
        year_stem = self.STEMS[year_stem_idx]
        year_branch = self.BRANCHES[year_branch_idx]
        
        # 日天干（用于排六神）- 简化计算，从已知日期推算
        # 1900年1月1日是癸亥日，可以从这个基准日计算
        base_date = datetime.datetime(1900, 1, 1)
        days_diff = (solar_date - base_date).days
        day_stem_idx = (days_diff + 9) % 10  # 1900/1/1是癸(10)，索引9
        day_stem = self.STEMS[day_stem_idx]
        
        return {
            'lunar_year': lunar.year,
            'lunar_month': lunar.month,
            'lunar_day': lunar.day,
            'year_branch_num': year_branch.number,
            'day_stem_num': day_stem.number,
            'hour_branch_num': hour_branch_num,
            'year_stem': year_stem,
            'year_branch': year_branch,
            'day_stem': day_stem,
            'lunar_str': f"{year_stem.chn_name}{year_branch.chn_name}年 {lunar.month}月{lunar.day}日"
        }
    
    def run_current_time(self):
        """
        使用当前时间自动起卦
        """
        now = datetime.datetime.now()
        print(f"\n当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        ganzhi_info = self.solar_to_ganzhi(now)
        print(f"农历: {ganzhi_info['lunar_str']}")
        print(f"时辰: {self.BRANCHES[ganzhi_info['hour_branch_num']-1].chn_name}时")
        print()
        
        self.run_date_method(
            year_branch_num=ganzhi_info['year_branch_num'],
            month=ganzhi_info['lunar_month'],
            day=ganzhi_info['lunar_day'],
            hour_branch_num=ganzhi_info['hour_branch_num'],
            day_stem_num=ganzhi_info['day_stem_num']
        )
    
    def run_solar_date(self, year: int, month: int, day: int, hour: int = 12):
        """
        使用阳历日期起卦
        
        Args:
            year: 阳历年
            month: 阳历月
            day: 阳历日
            hour: 小时（0-23）
        """
        solar_date = datetime.datetime(year, month, day, hour)
        print(f"\n阳历时间: {solar_date.strftime('%Y-%m-%d %H:%M')}")
        
        ganzhi_info = self.solar_to_ganzhi(solar_date)
        print(f"农历: {ganzhi_info['lunar_str']}")
        print(f"时辰: {self.BRANCHES[ganzhi_info['hour_branch_num']-1].chn_name}时")
        print()
        
        self.run_date_method(
            year_branch_num=ganzhi_info['year_branch_num'],
            month=ganzhi_info['lunar_month'],
            day=ganzhi_info['lunar_day'],
            hour_branch_num=ganzhi_info['hour_branch_num'],
            day_stem_num=ganzhi_info['day_stem_num']
        )

    def run_date_method(self, year_branch_num, month, day, hour_branch_num, day_stem_num):
        """
        Input:
        year_branch_num: 1(Zi) - 12(Hai)
        month: Lunar Month number
        day: Lunar Day number
        hour_branch_num: 1(Zi) - 12(Hai)
        day_stem_num: 1(Jia) - 10(Gui) -> Required for Six Gods
        """
        print(f"--- 日期起卦: 年支{year_branch_num}, 月{month}, 日{day}, 时支{hour_branch_num} ---")
        main, changed = LiuYaoEngine.method_date(year_branch_num, month, day, hour_branch_num)
        self.process_details(main, changed, day_stem_num)
        self.display(main, changed)

    def run_number_method(self, num1, num2, day_stem_num):
        print(f"--- 报数起卦: {num1}, {num2} ---")
        # PDF 1.2: Moving line is (a+b)%6
        moving = (num1 + num2) % 6
        if moving == 0: moving = 6
        
        main, changed = LiuYaoEngine.create_hexagram_from_numbers(
            num1 % 8 if num1 % 8 != 0 else 8,
            num2 % 8 if num2 % 8 != 0 else 8,
            moving
        )
        self.process_details(main, changed, day_stem_num)
        self.display(main, changed)

    def run_coin_method(self, coins: List[int], day_stem_num):
        """
        coins: List of 6 integers (0-3) representing 'Zheng' count from bottom to top
        """
        print(f"--- 钱币起卦: {coins} (下->上) ---")
        main, changed = LiuYaoEngine.method_coins(coins)
        self.process_details(main, changed, day_stem_num)
        self.display(main, changed)

    def process_details(self, main: Hexagram, changed: Hexagram, day_stem_num: int):
        # 1. Shi/Ying
        LiuYaoEngine.calculate_shi_ying(main)
        
        # 2. Palace
        LiuYaoEngine.calculate_palace(main)
        
        # 3. NaJia & Relatives (Main)
        day_stem = None
        for s in Stem:
            if s.number == day_stem_num:
                day_stem = s
                break
        
        LiuYaoEngine.calculate_najia_and_relatives(main, main.palace, day_stem)
        
        # 4. NaJia & Relatives (Changed) - Note: Changed hexagram relatives based on MAIN palace (usually)
        # But PDF implies simply calculating NaJia for changed. 
        # However, for Six Relatives comparison in Changed Hexagram, standard practice is comparing to Main Palace.
        # PDF Page 9 table implies Changed Hexagram lines have Relatives.
        # We will use Main Hexagram's Palace for Changed Hexagram's relative derivation logic to be consistent with standard Liu Yao.
        LiuYaoEngine.calculate_najia_and_relatives(changed, main.palace, day_stem)
        
        # 5. Six Gods (Only on Main)
        if day_stem:
            LiuYaoEngine.calculate_six_gods(main, day_stem)

    def get_hexagram_chart(self, main: Hexagram, changed: Hexagram, ganzhi_info: Dict) -> Dict:
        """
        Output the hexagram data for expert_agent in a structured dictionary.
        This provides all necessary details:
        - Main/Changed Hexagram (Name, Lines)
        - Shi/Ying (in Main)
        - Palace (Main)
        - NaJia (Stems/Branches for both)
        - Six Relatives (for both)
        - Flying/Hidden Spirits (Main)
        - Six Gods (Main)
        """
        
        def _fmt_line(line: Yao, is_main: bool, shi_idx: int = -1, ying_idx: int = -1):
            """Helper to format a single line"""
            data = {
                "position": line.position, # 1-6
                "yin_yang": "阳" if line.yin_yang == YinYang.YANG else "阴",
                "status": "动" if line.status == YaoStatus.MOVING else "静",
                "symbol": line.symbol_char,
                "stem": line.stem.chn_name if line.stem else "",
                "branch": line.branch.chn_name if line.branch else "",
                "wuxing": line.branch.element.value if line.branch else "",
                "relative": line.relative.value if line.relative else "",
            }
            
            if is_main:
                data["god"] = line.god.value if line.god else ""
                
                # Hidden Spirit (Fu Shen)
                if line.hidden_relative:
                    data["hidden"] = {
                        "relative": line.hidden_relative.value,
                        "branch": line.hidden_branch.chn_name if line.hidden_branch else "",
                        "stem": line.hidden_stem.chn_name if line.hidden_stem else "",
                        "wuxing": line.hidden_branch.element.value if line.hidden_branch else ""
                    }
                
                # Shi/Ying
                idx = line.position - 1
                if idx == shi_idx:
                    data["role"] = "世"
                elif idx == ying_idx:
                    data["role"] = "应"
                else:
                    data["role"] = ""
            
            return data

        # Prepare Main Hexagram Lines (ordered 6 -> 1 usually for display, but list implies 1->6 index wise. 
        # But 'lines' attribute is 0(Line1) to 5(Line6).
        # We will return them in order 1->6 but maybe consumption needs top-down. 
        # Let's return list 1->6 (index 0->5) for programmatic access, or matching display order? 
        # 'lines' attribute is 0-5. Let's keep that structure.
        
        main_lines_data = []
        for i in range(6):
            main_lines_data.append(_fmt_line(main.lines[i], True, main.shi_index, main.ying_index))
            
        changed_lines_data = []
        for i in range(6):
            changed_lines_data.append(_fmt_line(changed.lines[i], False))

        # Handle full name safely
        main_name = getattr(main, 'full_name', f"{main.upper_trigram.chn_name}{main.lower_trigram.chn_name}")
        changed_name = getattr(changed, 'full_name', f"{changed.upper_trigram.chn_name}{changed.lower_trigram.chn_name}")

        return {
            "date_info": {
                "solar": datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), # Or from input if stored
                "lunar_str": ganzhi_info.get('lunar_str', ''),
                "year_ganzhi": f"{ganzhi_info.get('year_stem', '').chn_name}{ganzhi_info.get('year_branch', '').chn_name}",
                "day_stem": ganzhi_info.get('day_stem', '').chn_name
            },
            "main_hexagram": {
                "name": main_name,
                "palace": main.palace.chn_name if main.palace else "",
                "lines": main_lines_data # Index 0 is Line 1
            },
            "changed_hexagram": {
                "name": changed_name,
                "lines": changed_lines_data
            }
        }

    def display(self, main: Hexagram, changed: Hexagram):
        print("\n" + "="*60)
        print(f"本卦: {main.full_name} (宫: {main.palace.chn_name if main.palace else '?'})")
        print(f"变卦: {changed.full_name}")
        print("="*60)
        
        print(f"{'六神':<6}{'伏神':<12}{'本卦':<16}{'六亲':<8}{'世应':<6}{'':<4}{'变卦':<16}{'六亲':<8}")
        print("-" * 80)
        
        # Print from Top (Line 6) to Bottom (Line 1)
        for i in range(5, -1, -1):
            m_line = main.lines[i]
            c_line = changed.lines[i]
            
            # 六神
            god_str = m_line.god.value if m_line.god else ""
            
            # 伏神
            fu_str = ""
            if m_line.hidden_relative:
                fu_str = f"{m_line.hidden_relative.value}{m_line.hidden_branch.chn_name}"
            
            # 本卦信息
            m_rel = m_line.relative.value if m_line.relative else ""
            m_stem_branch = f"{m_line.stem.chn_name if m_line.stem else ''}{m_line.branch.chn_name if m_line.branch else ''}"
            m_full = f"{m_line.symbol_char} {m_stem_branch}"
            
            # 世应
            sy_str = ""
            if main.shi_index == i: sy_str = "世"
            elif main.ying_index == i: sy_str = "应"
            
            # 变卦信息 (只有动爻才显示变卦，或者全部显示？PDF表格显示全部对应的纳甲，但通常只看动爻)
            # PDF Page 9 shows "变卦" column has NaJia even for static lines? 
            # Actually standard is only show changed lines. But PDF table fills all. I will fill all.
            c_rel = c_line.relative.value if c_line.relative else ""
            c_stem_branch = f"{c_line.stem.chn_name if c_line.stem else ''}{c_line.branch.chn_name if c_line.branch else ''}"
            c_full = f"{c_line.symbol_char} {c_stem_branch}"
            
            print(f"{god_str:<6}{fu_str:<12}{m_full:<16}{m_rel:<8}{sy_str:<6}{'->' if m_line.status == YaoStatus.MOVING else '  ':<4}{c_full:<16}{c_rel:<8}")

        print("="*60 + "\n")

# ==========================================
# 主程序入口 (Usage Example)
# ==========================================

if __name__ == "__main__":
    system = LiuYaoSystem()
    
    print("="*60)
    print("六爻排盘系统 - 使用示例")
    print("="*60)
    
    # 场景 1: 使用当前时间自动起卦（推荐）
    print("\n【场景 1: 当前时间自动起卦】")
    system.run_current_time()
    
    # 场景 2: 使用指定阳历日期起卦
    print("\n【场景 2: 指定阳历日期起卦】")
    system.run_solar_date(2025, 3, 2, 15)  # 2025年3月2日 15:00
    
    # 场景 3: 手动指定农历和干支（高级用户）
    print("\n【场景 3: 手动指定农历干支起卦】")
    system.run_date_method(
        year_branch_num=6, # 巳
        month=2, 
        day=2, 
        hour_branch_num=9, # 申
        day_stem_num=1 # 甲
    )
    
    # 场景 4: 报数排卦
    print("\n【场景 4: 报数起卦】")
    now = datetime.datetime.now()
    ganzhi = system.solar_to_ganzhi(now)
    system.run_number_method(5, 23, day_stem_num=ganzhi['day_stem_num'])
    
    # 场景 5: 钱币排卦
    print("\n【场景 5: 钱币起卦】")
    coins = [2, 2, 3, 1, 2, 0]  # 从初爻到上爻的正面数
    system.run_coin_method(coins, day_stem_num=ganzhi['day_stem_num'])
def calculate_hexagram(nums: List[int] = None, hour: int = None, tool_context: ToolContext = None) -> str:
    """
    根据输入的数字或当前时间进行六爻起卦排盘。
    
    Args:
        nums: (可选) 用户输入的数字列表。
              - 如果提供2个或以上数字，取前两个作为上卦和下卦数。
              - 动爻默认为 (两数之和) % 6。
        hour: (可选) 指定排盘的小时（0-23），如果不指定则使用当前时间。
        tool_context: ADK 工具上下文，用于存储排盘结果。
    """
    system = LiuYaoSystem()
    now = datetime.datetime.now()
    
    # Check for custom hour in session or argument
    target_hour = hour
    if target_hour is None and tool_context and tool_context.session:
        target_hour = tool_context.session.state.get("paipan_hour")
        
    if target_hour is not None:
         # Replace hour in 'now'
         # Note: system.solar_to_ganzhi computes stem/branch based on date, which is fine
         try:
             now = now.replace(hour=int(target_hour), minute=0, second=0)
         except ValueError:
             pass # Ignore invalid hour
    
    ganzhi_info = system.solar_to_ganzhi(now)
    day_stem_num = ganzhi_info['day_stem_num']

    main_hex = None
    changed_hex = None

    if nums and len(nums) >= 2:
        num1 = nums[0]
        num2 = nums[1]
        
        # Logic from run_number_method
        moving = (num1 + num2) % 6
        if moving == 0: moving = 6
        
        main_hex, changed_hex = LiuYaoEngine.create_hexagram_from_numbers(
            num1 % 8 if num1 % 8 != 0 else 8,
            num2 % 8 if num2 % 8 != 0 else 8,
            moving
        )
        mode = "数字起卦"
    else:
        # Time method
        main_hex, changed_hex = LiuYaoEngine.method_date(
            ganzhi_info['year_branch_num'],
            ganzhi_info['lunar_month'],
            ganzhi_info['lunar_day'],
            ganzhi_info['hour_branch_num']
        )
        mode = "时间起卦"

    # Process details (Najia, etc.)
    system.process_details(main_hex, changed_hex, day_stem_num)
    
    # Generate Chart Data source
    chart_data = system.get_hexagram_chart(main_hex, changed_hex, ganzhi_info)
    
    if tool_context and tool_context.session:
        tool_context.session.state["hexagram_chart"] = chart_data
        
    return f"已完成{mode}。本卦：{chart_data['main_hexagram']['name']}，变卦：{chart_data['changed_hexagram']['name']}。请专家进行解读。"
