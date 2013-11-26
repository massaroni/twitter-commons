python_binary(
  name = "thriftGenAngularService",
  source = "thriftGenAngularService.py",
  dependencies = [
    pants("src/python/twitter/common/app"),
    pants("src/python/twitter/thrift/descriptors"),
    pants("src/python/twitter/thrift/text"),
    python_requirement('jsonpickle')
  ]
)