import eeny

Rule110 = eeny.import_structs("components/rule110.eeny")
Cell1D = Rule110.AutomataCell1D
Demux = Rule110.Demux_1bit

N = 100

cells = [Cell1D(f"Cell{i+1}")[1] for i in range(N)]
temps = [Demux(f"Temp{i+1}")[1] for i in range(N)]

import random

for i in range(N):
    eeny.traverse(cells[i].Write1, 1)

# start at cell 0, demux 2 (skip first demux, assumed 0)

# chain demux, links neighbours (red)
for i in range(N - 1):
    curr = cells[i]
    next = cells[i + 1]

    curr.Demux1.Demux0.cycle = [next.Demux2.DemuxI]
    curr.Demux1.Demux1.cycle = [next.Demux3.DemuxI]
    curr.Demux2.Demux0.cycle = [next.Demux4.DemuxI]
    curr.Demux2.Demux1.cycle = [next.Demux5.DemuxI]
    curr.Demux3.Demux0.cycle = [next.Demux6.DemuxI]
    curr.Demux3.Demux1.cycle = [next.Demux7.DemuxI]

# with demuxed path, choose new state (pink)
for i in range(1, N):
    cell = cells[i]
    temp = temps[i - 1]

    cell.Zero.cycle = [temp.Write0]
    cell.One.cycle = [temp.Write1]

# write, and pass to next cell (orange)
for i in range(N):
    temp = temps[i]
    cell = cells[i]

    temp.Sig0.cycle = [cell.Demux1.DemuxI]
    temp.Sig1.cycle = [cell.Demux1.DemuxI]

# red, right edge case
cells[-1].Demux2.Demux0.cycle = [temps[-1].Write0]
cells[-1].Demux2.Demux1.cycle = [temps[-1].Write1]
cells[-1].Demux3.Demux0.cycle = [temps[-1].Write0]
cells[-1].Demux3.Demux1.cycle = [temps[-1].Write1]

# reset all top cells
temps[-1].Sig0.cycle = [cells[0].ResetI]
temps[-1].Sig1.cycle = [cells[0].ResetI]

for i in range(N - 1):
    curr = cells[i]
    next = cells[i + 1]

    curr.ResetO.cycle = [next.ResetI]

# mass rewrite temp to cell
cells[-1].ResetO.cycle = [temps[0].DemuxI]

for i in range(N - 1):
    temp = temps[i]
    cell = cells[i]
    next = temps[i + 1]

    temp.Demux0.cycle = [cell.Write0]
    temp.Demux1.cycle = [cell.Write1]
    cell.Sig0.cycle = [next.DemuxI]
    cell.Sig1.cycle = [next.DemuxI]

temps[-1].Demux0.cycle = [cells[-1].Write0]
temps[-1].Demux1.cycle = [cells[-1].Write1]

# reset all bottom cells

cells[-1].Sig0.cycle = [temps[0].ResetI]
cells[-1].Sig1.cycle = [temps[0].ResetI]

for i in range(N - 1):
    curr = temps[i]
    next = temps[i + 1]

    curr.ResetO.cycle = [next.ResetI]

# back to start
temps[-1].ResetO.cycle = [cells[0].Demux2.DemuxI]


def traverse(node, n):
    while True:
        # print("-", node, n)
        if str(node) == f"Temp{N}.ResetO":
            outp = []
            for cell in cells:
                outp.append("⬜⬛"[cell.Demux1.C.pos])
            print("".join(outp))

        if node is None or node.is_terminal:
            return node

        if n is eeny.Flags.inp_flag:
            n = ord(eeny.getch.getch())

        node, n = node.step(n)


end = traverse(cells[0].Demux2.DemuxI, 1)

#graph = eeny.extract_graph(cells[0].Demux2.DemuxI)
#eeny.dump_graph(graph, "rule110.eeny")