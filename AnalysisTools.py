import datetime
from enum import Enum
import ROOT
import os

class TauType(Enum):
  other = -1
  e = 0
  mu = 1
  tau = 2
  jet = 3
  emb_e = 4
  emb_mu = 5
  emb_tau = 6
  emb_jet = 7
  data = 8

def ListToVector(list, type="string"):
	vec = ROOT.std.vector(type)()
	for item in list:
		vec.push_back(item)
	return vec

def GenerateEnumCppString(cls):
  enum_string = f"enum class {cls.__name__} : int {{\n"
  for item in cls:
    enum_string += f"    {item.name} = {item.value},\n"
  enum_string += "};"
  return enum_string

def PrepareRootEnv():
  headers_dir = os.path.dirname(os.path.abspath(__file__))
  enums = [ TauType ]
  headers = [ 'AnalysisTools.h', 'GenLepton.h', 'GenTools.h', 'TupleMaker.h' ]
  for cls in enums:
    cls_str = GenerateEnumCppString(cls)
    if not ROOT.gInterpreter.Declare(cls_str):
      raise RuntimeError(f'Failed to declare {cls.__name__}')
  for header in headers:
    header_path = os.path.join(headers_dir, header)
    if not ROOT.gInterpreter.Declare(f'#include "{header_path}"'):
      raise RuntimeError(f'Failed to load {header_path}')

def timestamp_str():
  t = datetime.datetime.now()
  t_str = t.strftime('%Y-%m-%d %H:%M:%S')
  return f'[{t_str}] '

def MakeFileList(input):
  file_list = []
  if isinstance(input, str):
    input = input.split(',')
  for item in input:
    if not os.path.exists(item):
      raise RuntimeError(f'File or directory {item} does not exist')
    if os.path.isdir(item):
      for root, dirs, files in os.walk(item):
        for file in files:
          if file.endswith('.root'):
            file_list.append(os.path.join(root, file))
    else:
      file_list.append(item)
  return sorted(file_list)

def ApplyCommonDefinitions(df, deltaR=0.4, isData=False):
  df = df.Define("genLeptons", """reco_tau::gen_truth::GenLepton::fromNanoAOD(
                                    GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass,
                                    GenPart_genPartIdxMother, GenPart_pdgId, GenPart_statusFlags, event)""") \
         .Define('L1Tau_mass', 'RVecF(L1Tau_pt.size(), 0.)') \
         .Define('L1Tau_p4', 'GetP4(L1Tau_pt, L1Tau_eta, L1Tau_phi, L1Tau_mass)') \
         .Define('PFCand_p4','GetP4(PFCand_pt, PFCand_eta, PFCand_phi, PFCand_mass)')
  if isData:
    df = df.Define('L1Tau_type', 'RVecI(L1Tau_pt.size(), static_cast<int>(TauType::data))')
  else:
    df = df.Define('GenJet_p4', 'GetP4(GenJet_pt, GenJet_eta, GenJet_phi, GenJet_mass)') \
           .Define('GenLepton_p4', 'v_ops::visibleP4(genLeptons)') \
           .Define('L1Tau_genLepIndices', f'FindMatchingSet(L1Tau_p4, GenLepton_p4, {deltaR})') \
           .Define('L1Tau_genLepUniqueIdx', f'FindUniqueMatching(L1Tau_p4, GenLepton_p4, {deltaR})') \
           .Define('L1Tau_genJetUniqueIdx', f'FindUniqueMatching(L1Tau_p4, GenJet_p4, {deltaR})') \
           .Define('L1Tau_type', '''GetTauTypes(genLeptons, L1Tau_genLepUniqueIdx, L1Tau_genLepIndices,
                                                L1Tau_genJetUniqueIdx, false)''') \
           .Define('L1Tau_gen_p4', '''GetGenP4(L1Tau_type, L1Tau_genLepUniqueIdx, L1Tau_genJetUniqueIdx, genLeptons,
                                               GenJet_p4)''') \
           .Define('L1Tau_gen_pt', 'v_ops::pt(L1Tau_gen_p4)') \
           .Define('L1Tau_gen_eta', 'v_ops::eta(L1Tau_gen_p4)') \
           .Define('L1Tau_gen_abs_eta', 'abs(L1Tau_gen_eta)') \
           .Define('L1Tau_gen_phi', 'v_ops::phi(L1Tau_gen_p4)') \
           .Define('L1Tau_gen_mass', 'v_ops::mass(L1Tau_gen_p4)') \
           .Define('L1Tau_gen_charge', 'GetGenCharge(L1Tau_type, L1Tau_genLepUniqueIdx, genLeptons)') \
           .Define('L1Tau_gen_partonFlavour', '''GetGenPartonFlavour(L1Tau_type, L1Tau_genJetUniqueIdx,
                                                 GenJet_partonFlavour)''') 
  df = df.Define('L1Tau_PFCandIndices', f'FindMatchingSet(L1Tau_p4, PFCand_p4, {deltaR})')\
         .Define('L1Tau_PFCandUniqueIdx', f'FindUniqueMatching(L1Tau_p4, PFCand_p4, {deltaR})')\
         .Define('L1Tau_target_idx',f'FindAllMatching(L1Tau_p4, PFCand_p4, {deltaR})')\
         .Define('L1Tau_PFCand_pdgID','GetPFCandInt(L1Tau_target_idx,PFCand_pdgId)')\
         .Define('L1Tau_PFCand_charge','GetPFCandInt(L1Tau_target_idx,PFCand_charge)')\
         .Define('L1Tau_PFCand_EcalEnergy','GetPFCandFloat(L1Tau_target_idx,PFCand_EcalEnergy)')\
         .Define('L1Tau_PFCand_HcalEnergy','GetPFCandFloat(L1Tau_target_idx,PFCand_HcalEnergy)')\
         .Define('L1Tau_PFCand_eta','GetPFCandFloat(L1Tau_target_idx,PFCand_eta)')\
         .Define('L1Tau_PFCand_mass','GetPFCandFloat(L1Tau_target_idx,PFCand_mass)')\
         .Define('L1Tau_PFCand_phi','GetPFCandFloat(L1Tau_target_idx,PFCand_phi)')\
         .Define('L1Tau_PFCand_pt','GetPFCandFloat(L1Tau_target_idx,PFCand_pt)')\
         .Define('L1Tau_PFCand_rawEcalEnergy','GetPFCandFloat(L1Tau_target_idx,PFCand_rawEcalEnergy)')\
         .Define('L1Tau_PFCand_rawHcalEnergy','GetPFCandFloat(L1Tau_target_idx,PFCand_rawHcalEnergy)')\
         .Define('L1Tau_PFCand_trackChi2','GetPFCandFloat(L1Tau_target_idx,PFCand_trackChi2)')\
         .Define('L1Tau_PFCand_trackDxy','GetPFCandFloat(L1Tau_target_idx,PFCand_trackDxy)')\
         .Define('L1Tau_PFCand_trackDxyError','GetPFCandFloat(L1Tau_target_idx,PFCand_trackDxyError)')\
         .Define('L1Tau_PFCand_trackDz','GetPFCandFloat(L1Tau_target_idx,PFCand_trackDz)')\
         .Define('L1Tau_PFCand_trackDzError','GetPFCandFloat(L1Tau_target_idx,PFCand_trackDzError)')\
         .Define('L1Tau_PFCand_trackEta','GetPFCandFloat(L1Tau_target_idx,PFCand_trackEta)')\
         .Define('L1Tau_PFCand_trackEtaError','GetPFCandFloat(L1Tau_target_idx,PFCand_trackEtaError)')\
         .Define('L1Tau_PFCand_trackHitsValidFraction','GetPFCandFloat(L1Tau_target_idx,PFCand_trackHitsValidFraction)')\
         .Define('L1Tau_PFCand_trackNdof','GetPFCandFloat(L1Tau_target_idx,PFCand_trackNdof)')\
         .Define('L1Tau_PFCand_trackNumberOfLostHits','GetPFCandFloat(L1Tau_target_idx,PFCand_trackNumberOfLostHits)')\
         .Define('L1Tau_PFCand_trackNumberOfValidHits','GetPFCandFloat(L1Tau_target_idx,PFCand_trackNumberOfValidHits)')\
         .Define('L1Tau_PFCand_trackPhi','GetPFCandFloat(L1Tau_target_idx,PFCand_trackPhi)')\
         .Define('L1Tau_PFCand_trackPhiError','GetPFCandFloat(L1Tau_target_idx,PFCand_trackPhiError)')\
         .Define('L1Tau_PFCand_trackPt','GetPFCandFloat(L1Tau_target_idx,PFCand_trackPt)')\
         .Define('L1Tau_PFCand_trackPtError','GetPFCandFloat(L1Tau_target_idx,PFCand_trackPtError)')\
         .Define('L1Tau_PFCand_vx','GetPFCandFloat(L1Tau_target_idx,PFCand_vx)')\
         .Define('L1Tau_PFCand_vy','GetPFCandFloat(L1Tau_target_idx,PFCand_vy)')\
         .Define('L1Tau_PFCand_vz','GetPFCandFloat(L1Tau_target_idx,PFCand_vz)')
  return df
        #  .Define('L1Tau_PFCand_longLived','GetPFCandBool(L1Tau_PFCandUniqueIdx,PFCand_longLived)')\
        #  .Define('L1Tau_PFCand_trackIsValid','GetPFCandBool(L1Tau_PFCandUniqueIdx,PFCand_trackIsValid)')