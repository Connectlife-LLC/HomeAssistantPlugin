"""Parser for Hisense Washing Machine (025) device type."""
from typing import Dict

from .base import BaseDeviceParser, DeviceAttribute

from ..const import (
    StatusKey,
)

class HisenseWashingMachineParser(BaseDeviceParser):
    """Parser for Hisense Washing Machine."""
    
    @property
    def device_type(self) -> str:
        return "025"
        
    @property
    def feature_code(self) -> str:
        return "1wj105273v0w"


    @property
    def attributes(self) -> Dict[str, DeviceAttribute]:
          return {
            "Selected_program_remaining_time_in_minutes": DeviceAttribute(
                key=StatusKey.W_M_REMAINING_TIME,
                name="Selected program time remaining",
                attr_type="Number",
                step=1,
                value_range="0~800",
                read_write="R"
            ),             
            "WashingMachineState": DeviceAttribute(
                key=StatusKey.W_M_CURRENT_STATE,
                name="Washing machine state",
                attr_type="Enum",
                step=1,
                value_range="0~11",
                value_map={
                    "0": "Not Available",
                    "1": "Weight",
                    "2": "Prewash",
                    "3": "Mainwash",
                    "4": "Rinse",
                    "5": "Soften",
                    "6": "Anticrease",
                    "7": "Spin",
                    "8": "Dry",
                    "9": "Air",
                    "10": "Program end",
                    "11": "Delay",
                },
                read_write="R"
            ),
            "Status": DeviceAttribute(
                key=StatusKey.W_M_MACHINE_STATUS,
                name="Status",
                attr_type="Enum",
                step=1,
                value_range="0~4",
                value_map={
                    "0": "Standby",
                    "1": "Open",
                    "2": "Running",
                    "3": "Pause",
                    "4": "Error",
                },
                read_write="R"
            ),
        }