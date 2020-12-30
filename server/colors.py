COLOR_RED = "red"
COLOR_GREEN = "green"
COLOR_YELLOW = "yellow"
COLOR_BLUE = "blue"
COLOR_DEFUALT = "default"
COLOR_SEND = COLOR_YELLOW


COLORS = {
    COLOR_RED:"\u001b[31m",
    COLOR_GREEN:"\u001b[32m",
    COLOR_YELLOW:"\u001b[33m",
    COLOR_BLUE:"\u001b[34m",
    COLOR_DEFUALT:"\u001b[0m"
    }

def print_color(clr, msg):
    print(COLORS[clr]+msg+COLORS[COLOR_DEFUALT])

def colorize(clr, txt):
    return COLORS[clr]+txt+COLORS[COLOR_DEFUALT]