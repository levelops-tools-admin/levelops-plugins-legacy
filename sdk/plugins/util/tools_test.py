from tools import typechecked


class T1(object):
    @typechecked([str])
    def test(self, param):
        print("test: %s - %s" % (param, str(type(param)) ) )
    
    @typechecked([str])
    def failed(param):
        print("test: %s - %s" % (param, str(type(param)) ) )


@typechecked([str])
def test(param):
    print("test: %s" % str(type(param)))


@typechecked([str, int, int, str])
def test2(param: str, n: int, m: int, bye: str):
    print("test: (%s, %s, %s, %s)" % (str(type(param)), str(type(n)),str(type(m)),str(type(bye))) )


if __name__ == "__main__":
    test("hello1")
    test("hello2")
    test2("hello3", 3, 4, "yeii")
    T1().test("T1.test")
    try:
        T1().failed("T1.test")
    except TypeError as e:
        pass
    # test2(1)