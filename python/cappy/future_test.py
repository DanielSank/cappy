import pytest


import cappy.future as future


def test_callbacks():
    f = future.Future()
    a = []
    def callback(x):
        a.append('banana')
    f.add_callback(callback)
    f.set_result()
    assert a == ['banana']


def test_nested_future():

    square_value_holder = []
    def square(x):
        f = future.Future()
        square_value_holder.append(x**2)
        return f

    times_two_future_holder = []
    times_two_value_holder = []
    def times_two(x):
        f = future.Future()
        times_two_future_holder.append(f)
        times_two_value_holder.append(x*2)
        return f

    def simulate_handle_request(x):
        x_squared_future = square(x)
        x_squared_future.add_callback(times_two)
        return x_squared_future

    f = simulate_handle_request(3)
    f.set_result(square_value_holder[0])
    assert len(f.callbacks) == 0
    times_two_future = times_two_future_holder[0]
    assert len(times_two_future.callbacks) == 1
    times_two_future.set_result(times_two_value_holder[0])
    assert f.result == 18


def test_late_callback():
    f = future.Future()
    f.set_result(3)
    def callback(x):
        return x**2
    f.add_callback(callback)
    assert f.result == 9

