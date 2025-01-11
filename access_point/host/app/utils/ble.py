from enum import Enum

BLE_ADV_TYPE_NAME = "0x09"
BLE_ADV_TYPE_CHAR = "0x16"
BLE_TEMP_CHAR_UUID = "0x6E2A"
BLE_HUM_CHAR_UUID = "0x6F2A"
BLE_LOC_NORTH_CHAR_UUID = "0xB02A"
BLE_LOC_EAST_CHAR_UUID = "0xB12A"
BLE_BATTERY_LEVEL_CHAR_UUID = "0x192A"
BLE_SENSOR_PAWR_SERVICE_UUID = b"\xAA\xAA"
BLE_PAWR_SUBEVENT_CHAR_UUID = b"\xBB\xBB"
BLE_PAWR_RESPONSE_SLOT_CHAR_UUID = b"\xCC\xCC"

class PawrOpCodes(Enum):
    PING = 0
    READ_SENSOR_VALUES = 1

class ConnectionStates(Enum):
    CONNECTING = 0
    DISCOVER_SERVICES = 1
    DISCOVER_CHARACTERISTICS = 2
    WRITE_SUBEVENT = 3
    WRITE_RESPONSE_SLOT = 4
    PAST_TRANSFER = 5
            
class BleFsm():
    def __init__(self, initial_state):
        self._current_state = initial_state
        self._previous_state = None
        
    @property
    def current_state(self):
        return self._current_state
    
    @current_state.setter
    def current_state(self, new_state):
        self._previous_state = self._current_state
        self._current_state = new_state
    
    @property
    def previous_state(self):
        return self._previous_state
 
class ConnectionInfo():
    def __init__(self, ble_address, conn_handle):
        self.conn_handle = conn_handle
        self.ble_address = ble_address
        self.subevent = None
        self.pawr_addr = None
        self.service_handle = None
        self.char_handles = []
        self.state = None
        

def get_from_adv_data(adv_data, adv_type, char_uuid = None):
    adv_data_len = len(adv_data)
    i = 0
    while i < (adv_data_len - 1):
        found_adv_type_len = adv_data[i]
        found_adv_type = "0x{:02x}".format(adv_data[i+1])
        
        # If the wanted type is found in the adv data 
        if found_adv_type == adv_type:
            if char_uuid:
                uuid = adv_data[(i+2):(i+4):]
                uuid = "0x" + ''.join(f"{byte:02x}" for byte in uuid).upper()
                # If the uuid matches the wanted char_uuid
                if uuid == char_uuid:
                    char_data = adv_data[(i+4):(i+6):]
                    return char_data
            
            else:
                char_data = adv_data[(i+2):(i+found_adv_type_len+1):]
                char_data = ''.join(map(chr, char_data))
                return char_data
        
        i = i + found_adv_type_len + 1
    
    return None

def parse_char_data(char_data, return_type):
    lsb = char_data[0]
    msb = char_data[1]

    char_value = (msb << 8) | lsb

    if return_type == float:
        return_value = char_value / 100.0
    elif return_type == int:
        return_value = char_value

    return return_value
