import board
import rp2pio
import adafruit_pioasm

def i2s_ICS43434(fs=48000,nbits=32):
    in_pin   = board.D11
    bclk_pin = board.D9

    i2s_clock = fs * (2 * nbits)
    pio_clock = 2 * i2s_clock

    # special code for ICS43434
    if fs==48000:
        i2s_input = """
        .program pio_i2s_in 
        .side_set 2   ; 0 = bclk, 1=wclk
        ;                           +----- WCLK
        ;                           |+---- BCLK
            set x, 29        side 0b00 ; set bit count and WCLK
            nop              side 0b01
            nop              side 0b00
        left:
            in pins, 1       side 0b01
            jmp x--, left    side 0b00
            in null, 2       side 0b01  ; last is outside count
    
            set x, 30        side 0b10  ; set bit count and WCLK
        right:
            nop              side 0b11
            jmp x--, right   side 0b10
            nop              side 0b11
        """
    if fs==96000:
        i2s_input = """
        .program pio_i2s_in 
        .side_set 2   ; 0 = bclk, 1=wclk
        ;                           +----- WCLK
        ;                           |+---- BCLK
            set x, 28        side 0b00 ; set bit count and WCLK
            nop              side 0b01
            nop              side 0b00
            nop              side 0b01
            nop              side 0b00
        left:
            in pins, 1       side 0b01
            jmp x--, left    side 0b00
            in null, 3       side 0b01  ; last is outside count

            set x, 30        side 0b10  ; set bit count and WCLK
        right:
            nop              side 0b11
            jmp x--, right   side 0b10
            nop              side 0b11
        """

    pio_params = {
        "frequency": pio_clock,
        "first_in_pin": in_pin,
        "first_sideset_pin": bclk_pin,
        "sideset_pin_count": 2,
        "in_shift_right": False,
        "auto_push": True,
        "push_threshold": nbits
    }
    pio_instructions = adafruit_pioasm.assemble(i2s_input)
    #print(pio_instructions)
    sm = rp2pio.StateMachine(pio_instructions, **pio_params)
    return sm
