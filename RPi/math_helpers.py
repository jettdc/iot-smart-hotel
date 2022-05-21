def scale_angle_to_pwm_value(angle):
    angle_min, angle_max = 0, 180
    pwm_min, pwm_max = 5, 10

    # Algorithm to linearly scale between two ranges.
    # In our case, we input a value in the 0-180 range, then scale to the range 5-10
    # PWM: 5 is equivalent on the servo to -90 degrees, and 10 to 90 degrees, a total of 180 degrees
    result = pwm_min * (1 - ((angle - angle_min) / (angle_max - angle_min))) \
             + pwm_max * ((angle - angle_min) / (angle_max - angle_min))

    return math.floor(result)