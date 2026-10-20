"""Permit the exact Energy PF0 ink in the existing descriptor validator.

No raster code, SIO, resource format or allowlist changes.
"""
def install(source):
    f=source/'display.c'
    s=f.read_text()
    before='DESC[536]==238 && DESC[537]'
    assert s.count(before)==1
    f.write_text(s.replace(before,'DESC[536]==(area==1?40:238) && DESC[537]'))
