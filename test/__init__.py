import doctest
import unittest

import werkzeug

def find_all_modules(packages):
    for package in packages:
        yield package
        try:
            for module in werkzeug.find_modules(package, include_packages=True,
                                                recursive=True):
                yield module
        except ValueError, e:
            if e.args != ("'%s' is not a package" % package,):
                raise

def get_tests(packages):
    """
    Return a TestSuite
    """
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for module_name in find_all_modules(packages):
        suite.addTests(loader.loadTestsFromName(module_name))
        try:
            tests = doctest.DocTestSuite(module_name)
        except ValueError, e:
            # doctest.DocTestSuite throws ValueError when there is no test
            if len(e.args) != 2 or e.args[1] != "has no tests":
                raise
        else:
            suite.addTests(tests)
    return suite

def find_TODOs(packages):
    for module_name in find_all_modules(packages):
        if module_name == __name__:
            # prevent this script from finding itself
            continue
        filename = werkzeug.import_string(module_name).__file__
        if filename[-4:] in ('.pyc', '.pyo'):
            filename = filename[:-1]
        f = open(filename)
        todo_lines = []
        todo_count = 0
        for line_no, line in enumerate(f):
            count = line.count('TODO')
            if count:
                todo_count += count
                todo_lines.append(line_no + 1) # enumerate starts at 0
        f.close()
        if todo_count:
            yield filename, todo_count, todo_lines

def print_TODOs(packages):
    todos = list(find_TODOs(packages))
    if not todos:
        return # max() of an empty list raises an exception
    width = max(len(module) for module, count, lines in todos)
    for module, count, lines in todos:
        print '%-*s' % (width, module), ':', count,
        if count > 1:
            print 'TODOs on lines',
        else:
            print 'TODO  on line ',
        print ', '.join(str(line) for line in lines)

def run_tests(packages, verbosity=1):
    unittest.TextTestRunner(verbosity=verbosity).run(get_tests(packages))

def run_tests_with_coverage(packages, *args, **kwargs):
    import coverage
    try:
        # Coverage v3 API
        c = coverage.coverage()
    except coverage.CoverageException:
        # Coverage v2 API
        c = coverage

    c.exclude('raise NotImplementedError')
    c.exclude('except ImportError:')
    c.start()
    run_tests(packages, *args, **kwargs)
    c.stop()
    c.report([werkzeug.import_string(name).__file__ 
              for name in find_all_modules(p for p in packages if p != 'test')])


