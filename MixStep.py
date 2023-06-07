class MixStep:
  def Load(cfg):
    mix_steps = []
    pt_bin_edges = cfg['bin_edges']['pt']
    eta_bin_edges = cfg['bin_edges']['eta']
    batch_size = 0
    for bin_idx, bin in enumerate(cfg['bins']):
      #print("bin_idx: ",bin_idx)
      #print("bin:",bin)
      if len(bin['counts']) != len(pt_bin_edges) - 1:
        raise ValueError("Number of counts does not match number of pt bins")
      for pt_bin_idx, count in enumerate(bin['counts']):
        # print("the pt_bin_idx: ", pt_bin_idx)
        # print("counts: ", count)
        if count == 0: continue
        step = MixStep()
        # print("step: ",step)
        step.input_setups = bin['input_setups']
        # print("step.input_setups: ",step.input_setups)
        # 对于每一个步骤添加input_setup当中的文件名
        step.inputs = []
        for input_setup in bin['input_setups']:
          step.inputs.extend(cfg['inputs'][input_setup])
        #print("step.inputs: ",step.inputs)
        selection = cfg['bin_selection'].format(pt_low=pt_bin_edges[pt_bin_idx],
                                                pt_high=pt_bin_edges[pt_bin_idx + 1],
                                                eta_low=eta_bin_edges[bin['eta_bin']],
                                                eta_high=eta_bin_edges[bin['eta_bin'] + 1])
        # Give the selection for corresponding tau_type, eta_bin and pt_bin
        step.selection = f'L1Tau_type == static_cast<int>(TauType::{bin["tau_type"]}) && ({selection})'
        step.tau_type = bin['tau_type'] #对应的jet,tau或者electron
        step.eta_bin = bin['eta_bin'] # 对应于bins当中的eta_bin
        step.pt_bin = pt_bin_idx # 对应counts里的pt的index
        step.bin_idx = bin_idx
        step.start_idx = batch_size
        step.stop_idx = batch_size + count
        step.count = count # 对应于eta pt的bin当中的计数
        mix_steps.append(step)
        batch_size += count # 总的batch_size的大小
    return mix_steps, batch_size

  def Print(self):
    print(f'taus/batch: {self.count}')
    print(f'inputs: {self.input_setups}')
    print(f'eta bin: {self.eta_bin}')
    print(f'pt bin: {self.pt_bin}')
    print(f'bin idx: {self.bin_idx}')
    print(f'tau_type: {self.tau_type}')
    print(f'selection: {self.selection}')