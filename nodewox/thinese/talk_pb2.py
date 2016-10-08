# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: talk.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='talk.proto',
  package='thinese',
  syntax='proto3',
  serialized_pb=_b('\n\ntalk.proto\x12\x07thinese\"\x87\x01\n\x07Variant\x12\x11\n\x07int_val\x18\x01 \x01(\x05H\x00\x12\x12\n\x08real_val\x18\x02 \x01(\x02H\x00\x12\x12\n\x08\x62ool_val\x18\x03 \x01(\x08H\x00\x12\x11\n\x07\x62in_val\x18\x04 \x01(\x0cH\x00\x12\x11\n\x07str_val\x18\x05 \x01(\tH\x00\x12\x12\n\x08time_val\x18\x06 \x01(\x03H\x00\x42\x07\n\x05value\"4\n\x04Pair\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x1f\n\x05value\x18\x02 \x01(\x0b\x32\x10.thinese.Variant\"D\n\x06Packet\x12\x0b\n\x03src\x18\x01 \x01(\r\x12\x0b\n\x03gid\x18\x02 \x01(\r\x12 \n\x06values\x18\x03 \x03(\x0b\x32\x10.thinese.Variant\"\xa6\x02\n\x07Request\x12+\n\x06\x61\x63tion\x18\x01 \x01(\x0e\x32\x1b.thinese.Request.ActionType\x12,\n\x06params\x18\x02 \x03(\x0b\x32\x1c.thinese.Request.ParamsEntry\x12\x10\n\x08\x63hildren\x18\x03 \x03(\r\x1a?\n\x0bParamsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x1f\n\x05value\x18\x02 \x01(\x0b\x32\x10.thinese.Variant:\x02\x38\x01\"m\n\nActionType\x12\x16\n\x12\x41\x43TION_CHECK_ALIVE\x10\x00\x12\x16\n\x12\x41\x43TION_CHECK_PARAM\x10\x01\x12\x1c\n\x18\x41\x43TION_CHECK_PARAM_ALIVE\x10\x02\x12\x11\n\rACTION_CONFIG\x10\x03\"\x87\x02\n\x08Response\x12*\n\x07\x61\x63ktype\x18\x01 \x01(\x0e\x32\x19.thinese.Response.AckType\x12\x0c\n\x04\x63ode\x18\x02 \x01(\x05\x12\x0c\n\x04text\x18\x03 \x01(\t\x12-\n\x06params\x18\x0f \x03(\x0b\x32\x1d.thinese.Response.ParamsEntry\x1a?\n\x0bParamsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x1f\n\x05value\x18\x02 \x01(\x0b\x32\x10.thinese.Variant:\x02\x38\x01\"=\n\x07\x41\x63kType\x12\n\n\x06\x41\x43K_OK\x10\x00\x12\x0b\n\x07\x41\x43K_ERR\x10\x01\x12\x0c\n\x08\x41\x43K_DENY\x10\x02\x12\x0b\n\x07\x41\x43K_BYE\x10\x0fJ\x04\x08\x04\x10\x0f*W\n\x08\x44\x61taType\x12\n\n\x06\x44T_INT\x10\x00\x12\r\n\tDT_NUMBER\x10\x01\x12\x0b\n\x07\x44T_BOOL\x10\x02\x12\n\n\x06\x44T_BIN\x10\x03\x12\n\n\x06\x44T_STR\x10\x04\x12\x0b\n\x07\x44T_TIME\x10\x05\x62\x06proto3')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

_DATATYPE = _descriptor.EnumDescriptor(
  name='DataType',
  full_name='thinese.DataType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='DT_INT', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DT_NUMBER', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DT_BOOL', index=2, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DT_BIN', index=3, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DT_STR', index=4, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DT_TIME', index=5, number=5,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=848,
  serialized_end=935,
)
_sym_db.RegisterEnumDescriptor(_DATATYPE)

DataType = enum_type_wrapper.EnumTypeWrapper(_DATATYPE)
DT_INT = 0
DT_NUMBER = 1
DT_BOOL = 2
DT_BIN = 3
DT_STR = 4
DT_TIME = 5


_REQUEST_ACTIONTYPE = _descriptor.EnumDescriptor(
  name='ActionType',
  full_name='thinese.Request.ActionType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='ACTION_CHECK_ALIVE', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACTION_CHECK_PARAM', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACTION_CHECK_PARAM_ALIVE', index=2, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACTION_CONFIG', index=3, number=3,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=471,
  serialized_end=580,
)
_sym_db.RegisterEnumDescriptor(_REQUEST_ACTIONTYPE)

_RESPONSE_ACKTYPE = _descriptor.EnumDescriptor(
  name='AckType',
  full_name='thinese.Response.AckType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='ACK_OK', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACK_ERR', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACK_DENY', index=2, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACK_BYE', index=3, number=15,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=779,
  serialized_end=840,
)
_sym_db.RegisterEnumDescriptor(_RESPONSE_ACKTYPE)


_VARIANT = _descriptor.Descriptor(
  name='Variant',
  full_name='thinese.Variant',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='int_val', full_name='thinese.Variant.int_val', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='real_val', full_name='thinese.Variant.real_val', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='bool_val', full_name='thinese.Variant.bool_val', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='bin_val', full_name='thinese.Variant.bin_val', index=3,
      number=4, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='str_val', full_name='thinese.Variant.str_val', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='time_val', full_name='thinese.Variant.time_val', index=5,
      number=6, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='value', full_name='thinese.Variant.value',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=24,
  serialized_end=159,
)


_PAIR = _descriptor.Descriptor(
  name='Pair',
  full_name='thinese.Pair',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='thinese.Pair.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='value', full_name='thinese.Pair.value', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=161,
  serialized_end=213,
)


_PACKET = _descriptor.Descriptor(
  name='Packet',
  full_name='thinese.Packet',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='src', full_name='thinese.Packet.src', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='gid', full_name='thinese.Packet.gid', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='values', full_name='thinese.Packet.values', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=215,
  serialized_end=283,
)


_REQUEST_PARAMSENTRY = _descriptor.Descriptor(
  name='ParamsEntry',
  full_name='thinese.Request.ParamsEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='thinese.Request.ParamsEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='value', full_name='thinese.Request.ParamsEntry.value', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=_descriptor._ParseOptions(descriptor_pb2.MessageOptions(), _b('8\001')),
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=406,
  serialized_end=469,
)

_REQUEST = _descriptor.Descriptor(
  name='Request',
  full_name='thinese.Request',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='action', full_name='thinese.Request.action', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='params', full_name='thinese.Request.params', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='children', full_name='thinese.Request.children', index=2,
      number=3, type=13, cpp_type=3, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_REQUEST_PARAMSENTRY, ],
  enum_types=[
    _REQUEST_ACTIONTYPE,
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=286,
  serialized_end=580,
)


_RESPONSE_PARAMSENTRY = _descriptor.Descriptor(
  name='ParamsEntry',
  full_name='thinese.Response.ParamsEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='thinese.Response.ParamsEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='value', full_name='thinese.Response.ParamsEntry.value', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=_descriptor._ParseOptions(descriptor_pb2.MessageOptions(), _b('8\001')),
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=406,
  serialized_end=469,
)

_RESPONSE = _descriptor.Descriptor(
  name='Response',
  full_name='thinese.Response',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='acktype', full_name='thinese.Response.acktype', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='code', full_name='thinese.Response.code', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='text', full_name='thinese.Response.text', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='params', full_name='thinese.Response.params', index=3,
      number=15, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_RESPONSE_PARAMSENTRY, ],
  enum_types=[
    _RESPONSE_ACKTYPE,
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=583,
  serialized_end=846,
)

_VARIANT.oneofs_by_name['value'].fields.append(
  _VARIANT.fields_by_name['int_val'])
_VARIANT.fields_by_name['int_val'].containing_oneof = _VARIANT.oneofs_by_name['value']
_VARIANT.oneofs_by_name['value'].fields.append(
  _VARIANT.fields_by_name['real_val'])
_VARIANT.fields_by_name['real_val'].containing_oneof = _VARIANT.oneofs_by_name['value']
_VARIANT.oneofs_by_name['value'].fields.append(
  _VARIANT.fields_by_name['bool_val'])
_VARIANT.fields_by_name['bool_val'].containing_oneof = _VARIANT.oneofs_by_name['value']
_VARIANT.oneofs_by_name['value'].fields.append(
  _VARIANT.fields_by_name['bin_val'])
_VARIANT.fields_by_name['bin_val'].containing_oneof = _VARIANT.oneofs_by_name['value']
_VARIANT.oneofs_by_name['value'].fields.append(
  _VARIANT.fields_by_name['str_val'])
_VARIANT.fields_by_name['str_val'].containing_oneof = _VARIANT.oneofs_by_name['value']
_VARIANT.oneofs_by_name['value'].fields.append(
  _VARIANT.fields_by_name['time_val'])
_VARIANT.fields_by_name['time_val'].containing_oneof = _VARIANT.oneofs_by_name['value']
_PAIR.fields_by_name['value'].message_type = _VARIANT
_PACKET.fields_by_name['values'].message_type = _VARIANT
_REQUEST_PARAMSENTRY.fields_by_name['value'].message_type = _VARIANT
_REQUEST_PARAMSENTRY.containing_type = _REQUEST
_REQUEST.fields_by_name['action'].enum_type = _REQUEST_ACTIONTYPE
_REQUEST.fields_by_name['params'].message_type = _REQUEST_PARAMSENTRY
_REQUEST_ACTIONTYPE.containing_type = _REQUEST
_RESPONSE_PARAMSENTRY.fields_by_name['value'].message_type = _VARIANT
_RESPONSE_PARAMSENTRY.containing_type = _RESPONSE
_RESPONSE.fields_by_name['acktype'].enum_type = _RESPONSE_ACKTYPE
_RESPONSE.fields_by_name['params'].message_type = _RESPONSE_PARAMSENTRY
_RESPONSE_ACKTYPE.containing_type = _RESPONSE
DESCRIPTOR.message_types_by_name['Variant'] = _VARIANT
DESCRIPTOR.message_types_by_name['Pair'] = _PAIR
DESCRIPTOR.message_types_by_name['Packet'] = _PACKET
DESCRIPTOR.message_types_by_name['Request'] = _REQUEST
DESCRIPTOR.message_types_by_name['Response'] = _RESPONSE
DESCRIPTOR.enum_types_by_name['DataType'] = _DATATYPE

Variant = _reflection.GeneratedProtocolMessageType('Variant', (_message.Message,), dict(
  DESCRIPTOR = _VARIANT,
  __module__ = 'talk_pb2'
  # @@protoc_insertion_point(class_scope:thinese.Variant)
  ))
_sym_db.RegisterMessage(Variant)

Pair = _reflection.GeneratedProtocolMessageType('Pair', (_message.Message,), dict(
  DESCRIPTOR = _PAIR,
  __module__ = 'talk_pb2'
  # @@protoc_insertion_point(class_scope:thinese.Pair)
  ))
_sym_db.RegisterMessage(Pair)

Packet = _reflection.GeneratedProtocolMessageType('Packet', (_message.Message,), dict(
  DESCRIPTOR = _PACKET,
  __module__ = 'talk_pb2'
  # @@protoc_insertion_point(class_scope:thinese.Packet)
  ))
_sym_db.RegisterMessage(Packet)

Request = _reflection.GeneratedProtocolMessageType('Request', (_message.Message,), dict(

  ParamsEntry = _reflection.GeneratedProtocolMessageType('ParamsEntry', (_message.Message,), dict(
    DESCRIPTOR = _REQUEST_PARAMSENTRY,
    __module__ = 'talk_pb2'
    # @@protoc_insertion_point(class_scope:thinese.Request.ParamsEntry)
    ))
  ,
  DESCRIPTOR = _REQUEST,
  __module__ = 'talk_pb2'
  # @@protoc_insertion_point(class_scope:thinese.Request)
  ))
_sym_db.RegisterMessage(Request)
_sym_db.RegisterMessage(Request.ParamsEntry)

Response = _reflection.GeneratedProtocolMessageType('Response', (_message.Message,), dict(

  ParamsEntry = _reflection.GeneratedProtocolMessageType('ParamsEntry', (_message.Message,), dict(
    DESCRIPTOR = _RESPONSE_PARAMSENTRY,
    __module__ = 'talk_pb2'
    # @@protoc_insertion_point(class_scope:thinese.Response.ParamsEntry)
    ))
  ,
  DESCRIPTOR = _RESPONSE,
  __module__ = 'talk_pb2'
  # @@protoc_insertion_point(class_scope:thinese.Response)
  ))
_sym_db.RegisterMessage(Response)
_sym_db.RegisterMessage(Response.ParamsEntry)


_REQUEST_PARAMSENTRY.has_options = True
_REQUEST_PARAMSENTRY._options = _descriptor._ParseOptions(descriptor_pb2.MessageOptions(), _b('8\001'))
_RESPONSE_PARAMSENTRY.has_options = True
_RESPONSE_PARAMSENTRY._options = _descriptor._ParseOptions(descriptor_pb2.MessageOptions(), _b('8\001'))
# @@protoc_insertion_point(module_scope)
