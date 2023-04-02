"""
Chains many one bit demuxes together to create a n bit demux.
"""

n = 8
tab = "    "
outp = []

outp.append(f"Demux_{n}bit" " {")

for i in range(n):
    for j in range(2**i):
        outp.append(tab + f"Demux_{i+1}_{j} = Demux_1bit;")


# demux chain
outp.append("")
outp.append(tab + "DemuxI: Demux_1_0.DemuxI;")
for i in range(n - 1):
    for j in range(2**i):
        for k in range(2):
            outp.append(tab + f"Demux_{i+1}_{j}.Demux{k}: Demux_{i+2}_{j*2+k}.DemuxI;")

for j in range(2 ** (n - 1)):
    for k in range(2):
        outp.append(tab + f"Demux_{n}_{j}.Demux{k}: Demux_{bin(j*2+k)[2:].zfill(n)};")


for j in range(2**n):
    outp.append(tab + f"Demux_{bin(j)[2:].zfill(n)};")


# bit writing
for i in range(n):
    outp.append("")
    Xpattern = "X" * i + "0" + "X" * (n - i - 1)
    outp.append(tab + f"Write{Xpattern}: Demux_{i+1}_{0}.Write0;")

    for j in range(2**i - 1):
        outp.append(tab + f"Demux_{i+1}_{j}.Sig0: Demux_{i+1}_{j+1}.Write0;")
    outp.append(tab + f"Demux_{i+1}_{2 ** i - 1}.Sig0: Sig{Xpattern};")
    outp.append(tab + f"Sig{Xpattern};")

    Xpattern = "X" * i + "1" + "X" * (n - i - 1)
    outp.append(tab + f"Write{Xpattern}: Demux_{i+1}_{0}.Write1;")
    for j in range(2**i - 1):
        outp.append(tab + f"Demux_{i+1}_{j}.Sig1: Demux_{i+1}_{j+1}.Write1;")
    outp.append(tab + f"Demux_{i+1}_{2 ** i - 1}.Sig1: Sig{Xpattern};")
    outp.append(tab + f"Sig{Xpattern};")

# reset chain
outp.append("")
outp.append(tab + "ResetI: Demux_1_0.ResetI;")
prev = (1, 0)
for i in range(n):
    for j in range(2**i):
        if i == 0 and j == 0:
            continue
        outp.append(tab + f"Demux_{prev[0]}_{prev[1]}.ResetO: Demux_{i+1}_{j}.ResetI;")
        prev = (i + 1, j)
outp.append(tab + f"Demux_{prev[0]}_{prev[1]}.ResetO: ResetO;")
outp.append(tab + "ResetO;")

outp.append("}")

print("\n".join(outp), file=open("outp", "w+"))
