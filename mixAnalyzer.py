import os
import sys
import math
import numpy as np
import yaml

if __name__ == "__main__":
  file_dir = os.path.dirname(os.path.abspath(__file__))
  base_dir = os.path.dirname(file_dir)
  if base_dir not in sys.path:
    sys.path.append(base_dir)
  __package__ = os.path.split(file_dir)[-1]

from .AnalysisTools import *
from .MixStep import MixStep

#import ROOT
#ROOT.gROOT.SetBatch(True)
#ROOT.EnableThreadSafety()


def GetBinContent(hist, pt, eta):
  x_axis = hist.GetXaxis()
  x_bin = x_axis.FindFixBin(pt)
  y_axis = hist.GetYaxis()
  y_bin = y_axis.FindFixBin(eta)
  return hist.GetBinContent(x_bin, y_bin)

def analyse_mix(cfg_file):
  with open(cfg_file, 'r') as f:
    cfg = yaml.safe_load(f)
  mix_steps, batch_size = MixStep.Load(cfg)
  # 总的pt_eta的bin的读取数量
  print(f'Number of mix steps: {len(mix_steps)}')
  print(f'Batch size: {batch_size}')
  # step_stat用于记录每一个bin中可以算出的n_batches的数量
  # step_stat_split用于记录每一类当中的n_batches的数量
  step_stat = np.zeros(len(mix_steps))
  step_stat_split = { 'tau': np.zeros(len(mix_steps)), 'jet': np.zeros(len(mix_steps)), 'e': np.zeros(len(mix_steps)) }
  #print(step_stat_split)
  n_taus = { }
  n_taus_batch = { }
  # 对于每一个步骤（eta_pt的bin）
  for step_idx, step in enumerate(mix_steps):
    # print("step idx: ",step_idx," step: ", step)
    n_available = 0
    # 对于每一个步骤，读取相应的读取所有文件并对于相应eta pt的bin做计数
    for input in step.inputs:
      input_path = os.path.join(cfg['spectrum_root'], f'{input}.root')
      file = ROOT.TFile.Open(input_path, "READ")
      hist_name = f'pt_eta_{step.tau_type}'
      hist = file.Get(hist_name)
      # n_available 是每一个对应不同tau type的eta_pt的bin的计数
      n_available += hist.GetBinContent(step.pt_bin + 1, step.eta_bin + 1)
    n_taus[step.tau_type] = n_available + n_taus.get(step.tau_type, 0)
    # print("n_taus[step.tau_type]: ",n_taus[step.tau_type]," step.tau_type: ",step.tau_type)
    # print("step_idx: ",step_idx,"/ n_available:",n_available,"/ step.count:",step.count)
    n_taus_batch[step.tau_type] = step.count + n_taus_batch.get(step.tau_type, 0)
    # n_batches:计算每个eta与pt分bin中可以得到的batches的数量
    n_batches = math.floor(n_available / step.count)
    # step_stat：记录每个bin的batches数量
    step_stat[step_idx] = n_batches
    step_stat_split[step.tau_type][step_idx] = n_batches
  #print("step_stat:",step_stat)
  step_idx = np.argmin(step_stat)
  #print("step_idx:",step_idx)
  # 对于tau, jet 和 muon每一类的事例总数
  print(f'Total number of samples = {sum(n_taus.values())}: {n_taus}')
  # print("n_taus_batch:",n_taus_batch.items())
  # batches乘以一个batches当中的tau,jet和muon的事例数，得到总共使用的事例数
  # Konstantin认为tau的used fraction应该达到90%以上，所以数据还需要调整
  print("n_taus_batch:",n_taus_batch)
  n_taus_active = { name: x * step_stat[step_idx] for name, x in n_taus_batch.items()}
  #print("n_taus_active:",n_taus_active)
  print(f'Total number of used samples = {sum(n_taus_active.values())}: {n_taus_active}')
  n_taus_frac = { name: n_taus_active[name] / x for name, x in n_taus.items()}
  print(f'Used fraction: {n_taus_frac}')
  print(f'Number of samples per batch: {n_taus_batch}')
  n_taus_rel = { name: x / n_taus_batch['tau'] for name, x in n_taus_batch.items()}
  print(f'Relative number of samples: {n_taus_rel}')
  print('Step with minimum number of batches:')
  print(f'n_batches: {step_stat[step_idx]}')
  mix_steps[step_idx].Print()
  # print("step_stat_split:",step_stat_split)
  # 对于每一个tau_type计算最大的batch数量
  for name, stat in step_stat_split.items():
    step_idx = np.argmax(stat)
    print("step_idx:",step_idx)
    print(f'Step with maximum number of batches for {name}:')
    print(f'n_batches: {stat[step_idx]}')
    mix_steps[step_idx].Print()

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description='Make mix.')
  parser.add_argument('--cfg', required=True, type=str, help="Mix config file")
  args = parser.parse_args()

  analyse_mix(args.cfg)