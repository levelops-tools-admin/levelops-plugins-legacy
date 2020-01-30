import traceback

def typechecked(types: list):
    """ Validates position based arguments against expected types.

    Throws an exception in the case that an argument is not of the expected type.
    """
    def partial(func):
        def wrap(*args, **kwargs):
            validate_params(types=types, args=args)
            return func(*args, **kwargs)
        
        def class_wrap(self, *args, **kwargs):
            validate_params(types=types, args=args)
            try:
                return func(self, *args, **kwargs)
            except TypeError as e:
                raise TypeError("Seems like the method annotated is missing parameters... maybe 'self' as the reference to the class.\n %s" % str(e))
        if '.' in func.__qualname__:
             return class_wrap
        return wrap
    return partial


def validate_params(types, args):
    i = 0
    for t in types:
        a = args[i]
        if not isinstance(a, t):
            raise Exception("Argument '#%s' expected to be of type '%s' but was '%s'." % (i,t,str(type(a))))
        i += 1
