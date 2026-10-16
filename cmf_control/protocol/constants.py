# Packet framing — verified from APK decompilation (Message.java)
# SOF=0x55, control(2), command(2), length(2), fsn(1), payload(n), crc(2 if crc bit set)
SOF = 0x55
MAX_PAYLOAD = 512

# Control field flags
CTRL_CRC = 0x20        # bit 5 — CRC present
CTRL_MULTIFRAME = 0x40 # bit 6 — multi-frame

# Device type nibble in control field (bits 8-11, shifted)
# BudsLink sends 0x01 here (confirmed from nothingBudsSocket.js HEADER_MAGIC)
DEVICE_TYPE_CORSOLA = 1  # CMF Buds Pro 2 (codename: corsola)

# Command codes — verified from wi/v.java onUpdate() switch + am/s.java
# Both request and response use same command code; control.bits[0:4] == 0 means request
CMD_DEVICE_CONFIG      = 0xC006  # serial number, config (response: DeviceConfiguration)
CMD_BATTERY            = 0xC007  # battery levels (request: no payload; response: DeviceBattery)
CMD_IN_EAR_DETECTION   = 0xC00E  # wear detect enable/disable
CMD_NOISE_REDUCTION    = 0xC01E  # ANC / noise reduction get
CMD_NOISE_REDUCTION_SET = 0xF00F  # ANC / noise reduction set (different cmd!)
CMD_EQ_PRESET          = 0xC01F  # EQ preset index get
CMD_EQ_PRESET_SET      = 0xF010  # EQ preset index set
CMD_PERSONALIZED_ANC   = 0xC020  # personalised ANC
CMD_LOW_LATENCY        = 0xC041  # game/low-latency mode
CMD_FIRMWARE_VERSION   = 0xC001  # request firmware version
CMD_FIRMWARE_VERSION_R = 0xC042  # firmware version response/notify
CMD_BATTERY_NOTIFY     = 0xE001  # unsolicited battery notification (same data as C007)
CMD_NOISE_NOTIFY       = 0xE003  # unsolicited ANC state notification

# BLE service UUID — AEAC4A03-DFF5-498F-843A-34487CF133EB (cm/a.java)
SERVICE_UUID = "AEAC4A03-DFF5-498F-843A-34487CF133EB"

# OTA firmware RFCOMM UUID — 66666666-6666-6666-6666-666666666666 (ul/g.java)
OTA_UUID = "66666666-6666-6666-6666-666666666666"

# ANC / noise reduction modes — verified from DeviceNoiseReduction.java
# Payload format: repeated 3-byte tuples (type, value, none)
# type 1 = NOISE_REDUCTION_MODE, type 2 = NOISE_REDUCTION_LEVEL
ANC_MODE_STRONG        = 1    # value=1 (strong ANC)
ANC_MODE_MEDIUM        = 2    # value=2
ANC_MODE_WEAK          = 3    # value=3
ANC_MODE_SMART_1       = 4    # value=253 (0xFD)
ANC_MODE_OFF           = 5    # value=0
ANC_MODE_COMFORTABLE   = 6    # value=255 (0xFF)
ANC_MODE_PASS_THROUGH  = 7    # value=254 (0xFE)
ANC_MODE_SMART_2       = 8    # value=252 (0xFC)

# ANC encoded values (byte sent in payload)
# Verified from BudsLink CMFBudsPro2.js noiseControl
ANC_VAL_OFF            = 0x05
ANC_VAL_PASS_THROUGH   = 0x07  # transparency
ANC_VAL_STRONG         = 0x01  # high ANC
ANC_VAL_MEDIUM         = 0x02  # mid ANC
ANC_VAL_WEAK           = 0x03  # low ANC
ANC_VAL_ADAPTIVE       = 0x04  # adaptive ANC
# Old aliases kept for compat
ANC_VAL_SMART_2        = 0x04
ANC_VAL_SMART_1        = 0x04
ANC_VAL_COMFORTABLE    = 0x05

# EQ presets — verified from wi/v.java onUpdate() case 49183 (=0xC01F)
# Payload: single int (0-5)
EQ_BALANCED      = 0   # "sound_balanced"
EQ_MORE_VOICE    = 1   # "sound_more_voice"
EQ_MORE_TREBLE   = 2   # "sound_more_treble"
EQ_MORE_BASS     = 3   # "sound_more_bass"
EQ_CUSTOM        = 5   # "sound_eq_custom"

# Battery payload — DeviceBattery.java
# SparseArray keyed by: 1=watch, 2=left, 3=right, 4=case, 5=tws, 6=stereo
BATT_KEY_WATCH  = 1
BATT_KEY_LEFT   = 2
BATT_KEY_RIGHT  = 3
BATT_KEY_CASE   = 4
BATT_KEY_TWS    = 5
BATT_KEY_STEREO = 6
BATT_LEVEL_MASK    = 0x7F  # lower 7 bits = level
BATT_CHARGING_MASK = 0x80  # bit 7 = charging

# Backward-compat aliases (old names used in feature modules / tests)
CMD_GET_BATTERY    = CMD_BATTERY
CMD_GET_ANC        = CMD_NOISE_REDUCTION
CMD_SET_ANC        = CMD_NOISE_REDUCTION_SET
CMD_GET_EQ         = CMD_EQ_PRESET
CMD_SET_EQ         = 0xF01D  # LISTENING_MODE_SET (CMF Buds Pro 2 uses this, not EQ_SET)
CMD_GET_GESTURE    = 0xC018
CMD_SET_GESTURE    = 0xF003
CMD_IN_EAR_GET     = 0xC00E
CMD_IN_EAR_SET     = 0xF004
CMD_LATENCY_GET    = 0xC041
CMD_LATENCY_SET    = 0xF040
CMD_BASS_GET       = 0xC04E
CMD_BASS_SET       = 0xF051
CMD_SPATIAL_GET    = 0xC04F
CMD_SPATIAL_SET    = 0xF052

# Old ANC mode names mapped to verified values
ANC_OFF          = ANC_VAL_OFF
ANC_TRANSPARENCY = ANC_VAL_PASS_THROUGH
ANC_LIGHT        = ANC_VAL_STRONG        # approximate
ANC_MAX          = ANC_VAL_STRONG        # approximate — strong=1..127

# Old EQ names
EQ_BASS_BOOST    = EQ_MORE_BASS
EQ_TREBLE_BOOST  = EQ_MORE_TREBLE
EQ_PODCAST       = EQ_MORE_VOICE         # closest match
EQ_GAMING        = EQ_BALANCED           # no direct equivalent

# Gesture actions (not yet verified — still unconfirmed)
GESTURE_NONE         = 0x00
GESTURE_PLAY_PAUSE   = 0x01
GESTURE_NEXT_TRACK   = 0x02
GESTURE_PREV_TRACK   = 0x03
GESTURE_VOLUME_UP    = 0x04
GESTURE_VOLUME_DOWN  = 0x05
GESTURE_ANC_TOGGLE   = 0x06
GESTURE_VOICE_ASSIST = 0x07

# Gesture positions (not yet verified)
GESTURE_LEFT_SINGLE  = 0x10
GESTURE_LEFT_DOUBLE  = 0x11
GESTURE_LEFT_TRIPLE  = 0x12
GESTURE_LEFT_HOLD    = 0x13
GESTURE_RIGHT_SINGLE = 0x20
GESTURE_RIGHT_DOUBLE = 0x21
GESTURE_RIGHT_TRIPLE = 0x22
GESTURE_RIGHT_HOLD   = 0x23
