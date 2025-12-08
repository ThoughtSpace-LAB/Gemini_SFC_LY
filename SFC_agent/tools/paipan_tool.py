import datetime
import datetime
from google.adk.tools import ToolContext

class XiaoLiuRenPaipan:
    def __init__(self):
        # 基础常量定义
        self.PALACES = ["大安", "流连", "速喜", "赤口", "小吉", "空亡"]
        
        # 地支与五行对应 [cite: 1075]
        self.BRANCH_ELEMENTS = {
            "子": "水", "亥": "水",
            "寅": "木", "卯": "木",
            "巳": "火", "午": "火",
            "申": "金", "酉": "金",
            "丑": "土", "辰": "土", "未": "土", "戌": "土"
        }

        # 地支与六兽对应 [cite: 1052, 1053, 1062, 1064, 1065, 1066]
        # 寅卯青龙，巳午朱雀，丑辰勾陈，未戌腾蛇，申酉白虎，亥子玄武
        self.BRANCH_BEASTS = {
            "寅": "青龙", "卯": "青龙",
            "巳": "朱雀", "午": "朱雀",
            "丑": "勾陈", "辰": "勾陈",
            "未": "腾蛇", "戌": "腾蛇",
            "申": "白虎", "酉": "白虎",
            "亥": "玄武", "子": "玄武"
        }

        # 五行生克关系 [cite: 1073, 1074]
        self.ELEMENT_RELATIONS = {
            "水": {"生": "木", "克": "火"},
            "木": {"生": "火", "克": "土"},
            "火": {"生": "土", "克": "金"},
            "土": {"生": "金", "克": "水"},
            "金": {"生": "水", "克": "木"}
        }

    def get_shichen(self, hour: int) -> str:
        """根据小时获取地支时辰 [cite: 1042]"""
        if 23 <= hour or hour < 1: return "子"
        elif 1 <= hour < 3: return "丑"
        elif 3 <= hour < 5: return "寅"
        elif 5 <= hour < 7: return "卯"
        elif 7 <= hour < 9: return "辰"
        elif 9 <= hour < 11: return "巳"
        elif 11 <= hour < 13: return "午"
        elif 13 <= hour < 15: return "未"
        elif 15 <= hour < 17: return "申"
        elif 17 <= hour < 19: return "酉"
        elif 19 <= hour < 21: return "戌"
        else: return "亥" # 21-23点

    def step1_taiji_point(self, num1: int, num2: int) -> dict:
        """
        第一步: 定太极点 (AR-01-03)
        算法: (x + y - 1) mod 6 
        """
        # 注意：索引从0开始，而宫位是从1开始，所以计算索引时需要 -2
        # (num1 + num2 - 1) 是第几个宫位，转为列表索引需再 -1
        idx = (num1 + num2 - 2) % 6
        palace_name = self.PALACES[idx]
        return {"index": idx, "name": palace_name}

    def step2_assign_branches(self, current_shichen: str) -> list:
        """
        第二步: 取时辰、落宫位 (AR-01-04, AR-02-01)
        算法: 根据时辰定阴阳，取阴/阳进行宫位顺排 [cite: 1035]
        """
        # 定义阴阳属性 [cite: 1044]
        # 阴: 丑、卯、巳、未、酉、亥
        yin_branches = ["丑", "卯", "巳", "未", "酉", "亥"]
        # 阳: 子、寅、辰、午、申、戌
        yang_branches = ["子", "寅", "辰", "午", "申", "戌"]

        # 确定当前时辰是阴是阳
        is_yin = current_shichen in yin_branches

        # 确定落宫顺序
        # 文档示例中，如果是亥(阴)，顺序是: 酉、亥、丑、卯、巳、未 [cite: 1037]
        # 这表明阴的顺序是从酉开始隔位顺排，或者依据文档特定表格
        # 依据文档 Page 2-3 的表格推导：
        # 阴排盘顺序: 酉 -> 亥 -> 丑 -> 卯 -> 巳 -> 未
        target_sequence = ["酉", "亥", "丑", "卯", "巳", "未"] if is_yin else \
                          ["子", "寅", "辰", "午", "申", "戌"] # 阳顺排通常为子寅辰午申戌
        
        return target_sequence

    def step3_assign_beasts(self, palace_branches: list) -> list:
        """
        第三步: 定六兽 (AR-02-02)
        算法: 根据地支神兽对应关系落六兽 [cite: 1050]
        """
        beasts = []
        for branch in palace_branches:
            beasts.append(self.BRANCH_BEASTS[branch])
        return beasts

    def step4_assign_relations(self, palace_branches: list, taiji_index: int) -> list:
        """
        第四步: 定六亲 (AR-02-03)
        算法: 根据地支的生克关系排六亲，以太极点为基准 [cite: 1070, 1078]
        """
        # 1. 确定"我" (太极点落宫的地支)
        my_branch = palace_branches[taiji_index]
        my_element = self.BRANCH_ELEMENTS[my_branch]
        
        relations = []
        
        for branch in palace_branches:
            other_element = self.BRANCH_ELEMENTS[branch]
            
            # 判断生克关系 [cite: 1072]
            relation = ""
            if my_element == other_element:
                relation = "兄弟" # 同我
            elif self.ELEMENT_RELATIONS[my_element]["生"] == other_element:
                relation = "子孙" # 我生
            elif self.ELEMENT_RELATIONS[other_element]["生"] == my_element:
                relation = "父母" # 生我
            elif self.ELEMENT_RELATIONS[my_element]["克"] == other_element:
                relation = "妻财" # 我克
            elif self.ELEMENT_RELATIONS[other_element]["克"] == my_element:
                relation = "官鬼" # 克我
                
            relations.append(relation)
            
        return relations

    def run_calculation(self, num1: int, num2: int, current_hour: int = None) -> dict:
        """执行完整排盘逻辑"""
        # 0. 获取当前时辰
        if current_hour is None:
            current_hour = datetime.datetime.now().hour
        shichen = self.get_shichen(current_hour)

        # 1. 第一步：定太极点
        taiji = self.step1_taiji_point(num1, num2)
        
        # 2. 第二步：定地支 (落宫)
        branches = self.step2_assign_branches(shichen)
        
        # 3. 第三步：定六兽
        beasts = self.step3_assign_beasts(branches)
        
        # 4. 第四步：定六亲
        relations = self.step4_assign_relations(branches, taiji["index"])
        
        # 组装结果
        result_chart = []
        for i in range(6):
            is_taiji = (i == taiji["index"])
            result_chart.append({
                "index": i + 1,
                "palace": self.PALACES[i],      # 宫位名 (如大安)
                "branch": branches[i],          # 地支 (如酉)
                "beast": beasts[i],             # 六兽 (如白虎)
                "relation": relations[i],       # 六亲 (如父母)
                "is_taiji": is_taiji            # 是否为太极点(当前落宫)
            })
            
        return {
            "inputs": {"num1": num1, "num2": num2, "shichen": shichen},
            "taiji_info": taiji,
            "chart": result_chart
        }

def calculate_hexagram(nums: list[int], tool_context: ToolContext) -> dict:
    """
    根据用户输入的三个数字进行小六壬排盘。
    
    Args:
        nums: 包含两个整数的列表，例如 [78, 21]。第三个数字可选，用于指定时辰。
        tool_context: 工具上下文，用于存储状态。
        
    Returns:
        包含排盘结果的字典。
    """
    if len(nums) < 2:
        return {"error": "请输入至少两个数字"}
    
    # 取前两个数字进行排盘 (根据 run_calculation 的签名)
    num1 = nums[0]
    num2 = nums[1]
    
    paipan = XiaoLiuRenPaipan()
    
    # 执行排盘
    result = paipan.run_calculation(num1, num2)
    
    # 将结果存入 Session State
    tool_context.session.state["hexagram_chart"] = result
    
    return {"status": "success", "report": "排盘完成，数据已存入状态。", "data": result}

# --- 测试用例 (基于文档 Page 2-4 的举例) ---
if __name__ == "__main__":
    # 举例: 用户给数 1, 2 [cite: 1019]
    # 当前时辰为 亥 (21:00-23:00) [cite: 1032]
    
    calculator = XiaoLiuRenPaipan()
    # 假设 num1=1, num2=2, 22点是亥时
    result = calculator.run_calculation(1, 2, 22) 
    
    print(f"用户输入: {result['inputs']['num1']}, {result['inputs']['num2']}")
    print(f"当前时辰: {result['inputs']['shichen']}")
    print(f"太极点落: {result['taiji_info']['name']}")
    print("-" * 60)
    print(f"{'宫位':<6} {'地支':<6} {'六兽':<6} {'六亲':<6} {'状态'}")
    print("-" * 60)
    for row in result['chart']:
        marker = "<- 太极点 (我)" if row['is_taiji'] else ""
        print(f"{row['palace']:<6} {row['branch']:<6} {row['beast']:<6} {row['relation']:<6} {marker}")