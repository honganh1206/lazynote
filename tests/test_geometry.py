from antinote_qt.geometry import MIN_HEIGHT, MIN_WIDTH, Geometry, is_on_screen, parse_geometry

MON = Geometry(0, 0, 1920, 1080)


def test_accepts_window_fully_on_screen():
    assert is_on_screen(Geometry(100, 100, 360, 360), MON) is True


def test_rejects_window_off_screen():
    assert is_on_screen(Geometry(5000, 5000, 360, 360), MON) is False


def test_rejects_overlap_under_50px():
    assert is_on_screen(Geometry(-320, 100, 360, 360), MON) is False


def test_accepts_overlap_at_least_50px():
    assert is_on_screen(Geometry(-310, 100, 360, 360), MON) is True


def test_parse_none_and_empty():
    assert parse_geometry(None) is None
    assert parse_geometry("") is None


def test_parse_malformed_json():
    assert parse_geometry("{not json") is None


def test_parse_missing_or_wrong_type():
    assert parse_geometry('{"x":1,"y":2,"width":300}') is None
    assert parse_geometry('{"x":"1","y":2,"width":300,"height":300}') is None


def test_parse_valid_clamps_to_minimums():
    g = parse_geometry('{"x":10,"y":20,"width":100,"height":100}')
    assert g == Geometry(10, 20, MIN_WIDTH, MIN_HEIGHT)


def test_parse_keeps_sizes_above_minimum():
    g = parse_geometry('{"x":10,"y":20,"width":800,"height":600}')
    assert g == Geometry(10, 20, 800, 600)
