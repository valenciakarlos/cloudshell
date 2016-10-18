import re
import sys


def splice(f1, f2, tag, duptag=''):
    op = '<' + tag + '>'
    cl = '</' + tag + '>'

    if op not in f1 or op not in f2:
        return f1

    a, b = f1.split(op)
    attrs1, c = b.split(cl)

    _, x = f2.split('<' + tag + '>')
    attrs2, _ = x.split('</' + tag + '>')

    dd = '</' + duptag + '>'
    if duptag and dd in attrs1:
        a1 = set([re.findall(r'Name="[^"]*"', aa)[0] for aa in attrs1.split(dd) if aa.strip()])
        for aa in attrs2.split(dd):
            if not aa.strip():
                continue
            if re.findall(r'Name="[^"]*"', aa)[0] not in a1:
                attrs1 += aa + dd
    else:
        attrs1 += attrs2

    return a + op + attrs1 + cl + c


with open(sys.argv[1]) as f:
    f1 = f.read()

with open(sys.argv[2]) as f:
    f2 = f.read()

if 'ResourceTemplates' in f1:
    f1 = splice(f1, f2, 'ResourceTemplates')
else:
    f1 = splice(f1, f2, 'Attributes', 'AttributeInfo')
    f1 = splice(f1, f2, 'ResourceFamilies', 'ResourceFamily')
    f1 = splice(f1, f2, 'DriverDescriptors')

    # f1 = f1.replace('<DriverDescriptor DriverType="PythonDriver" Name="OnrackShellDriver" />', '<DriverDescriptor Name="OnrackShellDriver" DriverType="PythonDriver" />')
    # f1 = f1.replace('<DriverDescriptor DriverType="PythonDriver" Name="SiteManagerShellDriver" />', '<DriverDescriptor Name="SiteManagerShellDriver" DriverType="PythonDriver" />')
    # f1 = f1.replace('<DriverDescriptor DriverType="PythonDriver" Name="ComputeShellDriver" />', '<DriverDescriptor Name="ComputeShellDriver" DriverType="PythonDriver" />')


with open(sys.argv[1], 'w') as f:
    f.write(f1)