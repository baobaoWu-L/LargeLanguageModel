# from enum import Enum
# from typing import Optional, List, TypedDict, Any
# from pydantic import BaseModel, Field
#
# class LeaveType(str, Enum):
#     annual = "annual"      # 年假
#     sick = "sick"          # 病假
#     personal = "personal"  # 事假
#     other = "other"
#
# # 这个类表示的是请假单，模型就是一组数据
# # 模型类对应关系型数据库的表结构，一个对象对应表中的一行。这叫“对象-关系映射ORM”
# class LeaveRequest(BaseModel):
#     requester: str
#     leave_type: LeaveType = LeaveType.annual
#     start_time: Optional[str] = None  # "YYYYT-MM-DD HH:MM"
#     end_time: Optional[str] = None
#     duration_days: Optional[float] = None
#     reason: Optional[str] = None
#
#
# class LeaveState(TypedDict, total=False):
#     text: str
#     requester: str
#     user_role: str
#
#     req: dict            # LeaveRequest as dict
#     missing_fields: List[str]
#     violations: List[str]
#
#     answer: str
#     confirmed: bool
#     leave_id: Optional[str]  # LV-XXXXXXXX
#
#     user_id: Optional[int]
#     roles: List[str]
#     permissions: List[str]
#     is_super_admin: bool
#
#
