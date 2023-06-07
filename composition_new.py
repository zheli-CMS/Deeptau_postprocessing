import yaml
import os
import ROOT as R

def get_hist_count(hist, eta_min, eta_max, pt_min, pt_max):
    pt_bin_min = hist.GetXaxis().FindBin(pt_min)
    pt_bin_max = hist.GetXaxis().FindBin(pt_max) - 1
    eta_bin_min = hist.GetYaxis().FindBin(eta_min)
    eta_bin_max = hist.GetYaxis().FindBin(eta_max) - 1
    event_count = hist.Integral(pt_bin_min, pt_bin_max, eta_bin_min, eta_bin_max)  # 获取满足条件的事件数
    return event_count

def analyse_mix(cfg_file,run,run_yaml):
    with open(cfg_file, 'r') as f:
        config = yaml.safe_load(f)
    
    input_root = config['input_root']
    batch_size = config['batch_size']
    inputs = config['inputs']
    bin_selection = config['bin_selection']
    hist_names = config['hist_names']
    pt_list = config['bin_edges']['pt']
    eta_list = config['bin_edges']['eta']

    pt_lenth = len(pt_list)
    eta_lenth = len(eta_list)

    # The total number
    n_total = 0
    # The number of events for different type
    type_number = 0
    nevent_list = {}
    # Generate the list of event number
    for v_type in inputs:
        print(v_type)
    print(inputs)
    if run:
        for v_type in inputs:
            nevent_list[v_type] = {}
            for tau_type in hist_names:
                nevent_list[v_type][tau_type] = {}
                for pt in pt_list[:-1]:
                    nevent_list[v_type][tau_type][pt] = {}
                    for eta in eta_list[:-1]:
                        nevent_list[v_type][tau_type][pt][eta] = 0
        
        for v_type in inputs:
            for file_name in inputs[v_type]:
                input_file_name = os.path.join(input_root,file_name+'.root')
                print(input_file_name)
                input_file = R.TFile.Open(input_file_name)
                if input_file:
                    for hist_name in hist_names:
                        n_pt = 0
                        n_eta = 0
                        hist = input_file.Get(hist_name)
                        if hist:
                            while n_eta < (eta_lenth-1):
                                n_pt = 0
                                while n_pt < (pt_lenth-1):
                                    nevents = get_hist_count(hist,eta_list[n_eta],eta_list[n_eta+1],pt_list[n_pt],pt_list[n_pt+1])
                                    nevent_list[v_type][hist_name][pt_list[n_pt]][eta_list[n_eta]] += nevents
                                    n_total += nevents
                                    n_pt += 1
                                n_eta += 1
                        else:
                            print("Cannot find hist:", hist_name)
                else:
                    print("Cannot find file: ", input_file_name)
        print("The total number is: ", n_total)
        print("The original list is: ", nevent_list)
        for v_type in inputs:
            for tau_type in hist_names:
                for pt in pt_list[:-1]:
                    for eta in eta_list[:-1]:
                        nevent_list[v_type][tau_type][pt][eta] = round((nevent_list[v_type][tau_type][pt][eta]/n_total)*batch_size, 2)
        print("The processed nevent list is: ", nevent_list)
    # automatically generate the yaml file
    if run_yaml:
        bins = []
        for v_type in inputs:
            if v_type == "Higgs":
                continue
            elif v_type == "Zprime":
                for tau_type in hist_names:
                    if tau_type == 'pt_eta_mu':
                        continue
                    n_eta = 0
                    for eta in eta_list[:-1]: 
                        counts_ZprimeHiggs = []
                        for x in pt_list[:-1]:                 
                            value_ZprimeHiggs = round(nevent_list["Zprime"][tau_type][x][eta]) + round(nevent_list["Higgs"][tau_type][x][eta])
                            if value_ZprimeHiggs == 0:
                                if tau_type == "pt_eta_jet" or tau_type == "pt_eta_tau":
                                    value_ZprimeHiggs = 1
                            counts_ZprimeHiggs.append(value_ZprimeHiggs)
                        bin_data = {
                            'tau_type' : tau_type.replace("pt_eta_",""),
                            'eta_bin' : n_eta,
                            'counts' : str(counts_ZprimeHiggs),
                            'input_setups' : str(['Higgs','Zprime']),
                        }
                        n_eta += 1
                        bins.append(bin_data)
                    for eta in eta_list[:-1]: 
                        counts_ZprimeTTDY = []
                        for x in pt_list[:-1]: 
                            value_ZprimeTTDY = round(nevent_list["TT"][tau_type][x][eta]) + round(nevent_list["DY"][tau_type][x][eta])
                            if value_ZprimeTTDY == 0:
                                if tau_type == "pt_eta_jet" or tau_type == "pt_eta_tau":
                                    value_ZprimeTTDY = 1
                            counts_ZprimeTTDY.append(value_ZprimeTTDY)
                        bin_data = {
                            'tau_type' : tau_type.replace("pt_eta_",""),
                            'eta_bin' : n_eta,
                            'counts' : str(counts_ZprimeTTDY),
                            'input_setups' : str(['Higgs','TT','Zprime']),
                        }
                        n_eta += 1
                        bins.append(bin_data)
            else:
                for tau_type in hist_names:
                    if tau_type == 'pt_eta_mu':
                        continue
                    n_eta = 0
                    for eta in eta_list[:-1]:
                        # print([ nevent_list[v_type][tau_type][x][eta] for x in pt_list[:-1]])
                        counts_list = []
                        for x in pt_list[:-1]:
                            value = round(nevent_list[v_type][tau_type][x][eta])
                            if value == 0:
                                if tau_type == "pt_eta_jet" or tau_type == "pt_eta_tau":
                                    value = 1
                            counts_list.append(value)
                        bin_data = {
                            'tau_type' : tau_type.replace("pt_eta_",""),
                            'eta_bin' : n_eta,
                            'counts' : str(counts_list),
                            'input_setups' : v_type ,
                        }
                        n_eta += 1
                        bins.append(bin_data)
        yaml_data = yaml.dump({'bins':bins},indent=4)

        with open('data.yaml','w') as file:
            file.write(yaml_data)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Make mix.')
    parser.add_argument('--cfg', required=True, type=str, help="Mix config file")
    parser.add_argument('--run', required=0, type=int, help="Run the composition calculation?")
    parser.add_argument('--run_yaml', required=0, type=int, help="Create the yaml file for composition?")
    args = parser.parse_args()

    analyse_mix(args.cfg,args.run,args.run_yaml)