# pydebuginfod

pydebuginfod is a Python client implementation of the [debuginfod
spec](https://www.mankier.com/8/debuginfod).

```python
import debuginfod
dbginfo = debuginfod.get("c0e8c127f1f36dd10e77331f46b6e2dbbbdb219b")
dbginfo
>>> '/home/matt/.cache/debuginfod/buildid/c0e8c127f1f36dd10e77331f46b6e2dbbbdb219b/debuginfo'
```

pydebuginfod allows you to easily get started with debuginfod.