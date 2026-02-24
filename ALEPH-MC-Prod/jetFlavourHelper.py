import sys
import json
import ROOT

ROOT.gROOT.SetBatch(True)

class JetFlavourHelper:
    def __init__(self, jet, jetc, tag=""):

        self.jet = jet
        self.const = jetc

        self.tag = tag
        if tag != "":
            self.tag = "_{}".format(tag)

        self.coll = {
            "GenParticles": "MCParticles",
            "PFParticles": "RecoParticles",
            "PFTracks": "EFlowTrack",
            "PFPhotons": "EFlowPhoton",
            "PFNeutralHadrons": "EFlowNeutralHadron",
            "TrackState": "_Tracks_trackStates",
            "TrackerHits": "TrackerHits",
            "CalorimeterHits": "CalorimeterHits",
            "PathLength": "EFlowTrack_L",
            "Bz": "magFieldBz",
        }

        self.definition = dict()

        # ===== TRACK LEVEL
        self.definition["n_tracks_all{}".format(self.tag)] = "Tracks.size()"
        self.definition["chi2_tracks_all{}".format(self.tag)] = "AlephSelection::get_track_chi2( Tracks )"
        self.definition["ndf_tracks_all{}".format(self.tag)] = "AlephSelection::get_track_ndf( Tracks )"
        self.definition["chi2_o_ndf_tracks_all{}".format(self.tag)] = "AlephSelection::get_track_ndf( Tracks )"

        # baseline track selection
        self.definition["tracks_selected_baseline_result{}".format(self.tag)] = "AlephSelection::select_tracks_baseline( Tracks, {} )".format(self.coll["TrackState"])
        self.definition["tracks_selected_baseline{}".format(self.tag)] = "tracks_selected_baseline_result{}.tracks".format(self.tag)
        self.definition["trackstates_selected_baseline{}".format(self.tag)] = "tracks_selected_baseline_result{}.trackStates".format(self.tag)

        # impact parameter selection for vertex fit
        self.definition["tracks_selected_for_vertexfit_result{}".format(self.tag)] = "AlephSelection::select_tracks_impactparameters( tracks_selected_baseline_result{}, 0.75, 2.0 )".format(self.tag)
        self.definition["tracks_selected_for_vertexfit{}".format(self.tag)] = "tracks_selected_for_vertexfit_result{}.tracks".format(self.tag)
        self.definition["trackstates_selected_for_vertexfit{}".format(self.tag)] = "tracks_selected_for_vertexfit_result{}.trackStates".format(self.tag)
        self.definition["n_tracks_sel{}".format(self.tag)] = "tracks_selected_baseline{}.size()".format(self.tag)
        self.definition["n_trackstates_sel{}".format(self.tag)] = "trackstates_selected_baseline{}.size()".format(self.tag)
        self.definition["n_tracks_sel_vertexfit{}".format(self.tag)] = "tracks_selected_for_vertexfit{}.size()".format(self.tag)

        # ===== VERTEX
        res_x_loose = 200.  # in um
        res_y_loose = 100.  # in um
        res_z_loose = 2.    # in cm
        chi2max = 5.

        self.definition["RecoedPrimaryTracks_looseBS{}".format(self.tag)] = "VertexFitterSimple::get_PrimaryTracks(trackstates_selected_for_vertexfit{}, true, {},{},{},0.,0.,0., {})".format(
            self.tag, res_x_loose/10., res_y_loose/10., res_z_loose*1E03, chi2max)
        self.definition["VertexObject_looseBS{}".format(self.tag)] = "VertexFitterSimple::VertexFitter_Tk(1, RecoedPrimaryTracks_looseBS{}, true, {},{},{},0.,0.,0.)".format(
            self.tag, res_x_loose/10., res_y_loose/10., res_z_loose*1E03)
        self.definition["Vertex_refit_looseBS{}".format(self.tag)] = "VertexingUtils::get_VertexData(VertexObject_looseBS{})".format(self.tag)
        self.definition["Vertex_refit_tlv{}".format(self.tag)] = "TLorentzVector(Vertex_refit_looseBS{}.position.x, Vertex_refit_looseBS{}.position.y, Vertex_refit_looseBS{}.position.z, 0.)".format(self.tag, self.tag, self.tag)
        self.definition["SecondaryTracks_looseBS{}".format(self.tag)] = "VertexFitterSimple::get_NonPrimaryTracks(trackstates_selected_baseline{}, RecoedPrimaryTracks_looseBS{})".format(self.tag, self.tag)
        self.definition["Vertex_refit_x{}".format(self.tag)] = "Vertex_refit_looseBS{}.position.x".format(self.tag)
        self.definition["Vertex_refit_y{}".format(self.tag)] = "Vertex_refit_looseBS{}.position.y".format(self.tag)
        self.definition["Vertex_refit_z{}".format(self.tag)] = "Vertex_refit_looseBS{}.position.z".format(self.tag)
        self.definition["n_primary_tracks{}".format(self.tag)] = "ReconstructedParticle2Track::getTK_n(RecoedPrimaryTracks_looseBS{})".format(self.tag)
        self.definition["n_secondary_tracks{}".format(self.tag)] = "ReconstructedParticle2Track::getTK_n(SecondaryTracks_looseBS{})".format(self.tag)
        self.definition["pv{}".format(self.tag)] = "TLorentzVector(Vertices[0].position.x, Vertices[0].position.y, Vertices[0].position.z, 0.0)"
        self.definition["VertexX{}".format(self.tag)] = "Vertices.position.x"
        self.definition["VertexY{}".format(self.tag)] = "Vertices.position.y"
        self.definition["VertexZ{}".format(self.tag)] = "Vertices.position.z"

        # ===== PARTICLE FLOW TYPE FLAGS
        self.definition["pfcand_isMu{}".format(self.tag)] = "AlephSelection::get_isType(jetConstitutentsTypes, 2)"
        self.definition["pfcand_isEl{}".format(self.tag)] = "AlephSelection::get_isType(jetConstitutentsTypes, 1)"
        self.definition["pfcand_isGamma{}".format(self.tag)] = "AlephSelection::get_isType(jetConstitutentsTypes, 4)"
        self.definition["pfcand_isChargedHad{}".format(self.tag)] = "AlephSelection::get_isType(jetConstitutentsTypes, 0)"
        self.definition["pfcand_isNeutralHad{}".format(self.tag)] = "AlephSelection::get_isType(jetConstitutentsTypes, 5)"

        # ===== KINEMATICS AND PID
        self.definition["pfcand_e{}".format(self.tag)] = "JetConstituentsUtils::get_e({})".format(self.const)
        self.definition["pfcand_p{}".format(self.tag)] = "JetConstituentsUtils::get_p({})".format(self.const)
        self.definition["pfcand_px{}".format(self.tag)] = "AlephSelection::get_px({})".format(self.const)
        self.definition["pfcand_py{}".format(self.tag)] = "AlephSelection::get_py({})".format(self.const)
        self.definition["pfcand_pz{}".format(self.tag)] = "AlephSelection::get_pz({})".format(self.const)
        self.definition["pfcand_mask{}".format(self.tag)] = "AlephSelection::mask(pfcand_e{})".format(self.tag)
        self.definition["pfcand_theta{}".format(self.tag)] = "JetConstituentsUtils::get_theta({})".format(self.const)
        self.definition["pfcand_phi{}".format(self.tag)] = "JetConstituentsUtils::get_phi({})".format(self.const)
        self.definition["pfcand_charge{}".format(self.tag)] = "JetConstituentsUtils::get_charge({})".format(self.const)
        self.definition["pfcand_type{}".format(self.tag)] = "JetConstituentsUtils::get_type({})".format(self.const)
        self.definition["pfcand_erel{}".format(self.tag)] = "JetConstituentsUtils::get_erel_cluster({}, {})".format(self.jet, self.const)
        self.definition["pfcand_erel_log{}".format(self.tag)] = "JetConstituentsUtils::get_erel_log_cluster({}, {})".format(self.jet, self.const)
        self.definition["pfcand_thetarel{}".format(self.tag)] = "JetConstituentsUtils::get_thetarel_cluster({}, {})".format(self.jet, self.const)
        self.definition["pfcand_phirel{}".format(self.tag)] = "JetConstituentsUtils::get_phirel_cluster({}, {})".format(self.jet, self.const)
        self.definition["Bz{}".format(self.tag)] = "1.5"

        # ===== TRACK PARAMETERS
        self.definition["TrackStateFlipped{}".format(self.tag)] = "AlephSelection::flipSign_copy( {} )".format(self.coll["TrackState"])
        self.definition["pfcand_dxy{}".format(self.tag)] = "JetConstituentsUtils::XPtoPar_dxy({}, TrackStateFlipped{}, Vertex_refit_tlv{}, Bz{})".format(self.const, self.tag, self.tag, self.tag)
        self.definition["pfcand_dz{}".format(self.tag)] = "JetConstituentsUtils::XPtoPar_dz({}, TrackStateFlipped{}, Vertex_refit_tlv{}, Bz{})".format(self.const, self.tag, self.tag, self.tag)
        self.definition["pfcand_phi0{}".format(self.tag)] = "JetConstituentsUtils::XPtoPar_phi({}, TrackStateFlipped{}, Vertex_refit_tlv{}, Bz{})".format(self.const, self.tag, self.tag, self.tag)
        self.definition["pfcand_C{}".format(self.tag)] = "JetConstituentsUtils::XPtoPar_C({}, TrackStateFlipped{}, Bz{})".format(self.const, self.tag, self.tag)
        self.definition["pfcand_ct{}".format(self.tag)] = "JetConstituentsUtils::XPtoPar_ct({}, TrackStateFlipped{}, Bz{})".format(self.const, self.tag, self.tag)
        self.definition["pfcand_dptdpt{}".format(self.tag)] = "JetConstituentsUtils::get_omega_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_dxydxy{}".format(self.tag)] = "JetConstituentsUtils::get_d0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_dzdz{}".format(self.tag)] = "JetConstituentsUtils::get_z0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_dphidphi{}".format(self.tag)] = "JetConstituentsUtils::get_phi0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_detadeta{}".format(self.tag)] = "JetConstituentsUtils::get_tanlambda_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_dxydz{}".format(self.tag)] = "JetConstituentsUtils::get_d0_z0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_dphidxy{}".format(self.tag)] = "JetConstituentsUtils::get_phi0_d0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_phidz{}".format(self.tag)] = "JetConstituentsUtils::get_phi0_z0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_phictgtheta{}".format(self.tag)] = "JetConstituentsUtils::get_tanlambda_phi0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_dxyctgtheta{}".format(self.tag)] = "JetConstituentsUtils::get_tanlambda_d0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_dlambdadz{}".format(self.tag)] = "JetConstituentsUtils::get_tanlambda_z0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_cctgtheta{}".format(self.tag)] = "JetConstituentsUtils::get_omega_tanlambda_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_phic{}".format(self.tag)] = "JetConstituentsUtils::get_omega_phi0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_dxyc{}".format(self.tag)] = "JetConstituentsUtils::get_omega_d0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)
        self.definition["pfcand_cdz{}".format(self.tag)] = "JetConstituentsUtils::get_omega_z0_cov({}, TrackStateFlipped{})".format(self.const, self.tag)

        # ===== BTAG VARIABLES
        self.definition["pfcand_btagSip2dVal{}".format(self.tag)] = "JetConstituentsUtils::get_Sip2dVal_clusterV({}, pfcand_dxy{}, pfcand_phi0{}, Bz{})".format(self.jet, self.tag, self.tag, self.tag)
        self.definition["pfcand_btagSip2dSig{}".format(self.tag)] = "JetConstituentsUtils::get_Sip2dSig(pfcand_btagSip2dVal{}, pfcand_dxydxy{})".format(self.tag, self.tag)
        self.definition["pfcand_btagSip3dVal{}".format(self.tag)] = "JetConstituentsUtils::get_Sip3dVal_clusterV({}, pfcand_dxy{}, pfcand_dz{}, pfcand_phi0{}, Bz{})".format(self.jet, self.tag, self.tag, self.tag, self.tag)
        self.definition["pfcand_btagSip3dSig{}".format(self.tag)] = "JetConstituentsUtils::get_Sip3dSig(pfcand_btagSip3dVal{}, pfcand_dxydxy{}, pfcand_dzdz{})".format(self.tag, self.tag, self.tag)
        self.definition["pfcand_btagJetDistVal{}".format(self.tag)] = "JetConstituentsUtils::get_JetDistVal_clusterV({}, {}, pfcand_dxy{}, pfcand_dz{}, pfcand_phi0{}, Bz{})".format(self.jet, self.const, self.tag, self.tag, self.tag, self.tag)
        self.definition["pfcand_btagJetDistSig{}".format(self.tag)] = "JetConstituentsUtils::get_JetDistSig(pfcand_btagJetDistVal{}, pfcand_dxydxy{}, pfcand_dzdz{})".format(self.tag, self.tag, self.tag)

        # ===== dEdx / PID (Pads)
        self.definition["jet_constituents_dEdx_PIDhypo_pads_result{}".format(self.tag)] = "AlephSelection::build_constituents_dEdx_PIDhypo()({}, _RecoParticles_tracks.index, dEdxPads, _dEdxPads_track.index, _{}, false)".format(self.coll["PFParticles"], self.const)
        self.definition["jet_constituents_dEdx_pads_objs{}".format(self.tag)] = "jet_constituents_dEdx_PIDhypo_pads_result{}.dedx_constituents".format(self.tag)
        self.definition["pfcand_dEdx_pads_type{}".format(self.tag)] = "AlephSelection::get_dEdx_type(jet_constituents_dEdx_pads_objs{})".format(self.tag)
        self.definition["pfcand_dEdx_pads_value{}".format(self.tag)] = "AlephSelection::get_dEdx_value(jet_constituents_dEdx_pads_objs{})".format(self.tag)
        self.definition["pfcand_dEdx_pads_error{}".format(self.tag)] = "AlephSelection::get_dEdx_error(jet_constituents_dEdx_pads_objs{})".format(self.tag)
        self.definition["jet_constituents_PID_pvals_pads{}".format(self.tag)] = "jet_constituents_dEdx_PIDhypo_pads_result{}.pid_array_constituents".format(self.tag)
        self.definition["pfcand_PID_pval_pads_ele{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_pads{}, 0)".format(self.tag)
        self.definition["pfcand_PID_pval_pads_mu{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_pads{}, 1)".format(self.tag)
        self.definition["pfcand_PID_pval_pads_pi{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_pads{}, 2)".format(self.tag)
        self.definition["pfcand_PID_pval_pads_kaon{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_pads{}, 3)".format(self.tag)
        self.definition["pfcand_PID_pval_pads_proton{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_pads{}, 4)".format(self.tag)

        # ===== dEdx / PID (Wires)
        self.definition["jet_constituents_dEdx_PIDhypo_wires_result{}".format(self.tag)] = "AlephSelection::build_constituents_dEdx_PIDhypo()({}, _RecoParticles_tracks.index, dEdxWires, _dEdxWires_track.index, _{}, true)".format(self.coll["PFParticles"], self.const)
        self.definition["jet_constituents_dEdx_wires_objs{}".format(self.tag)] = "jet_constituents_dEdx_PIDhypo_wires_result{}.dedx_constituents".format(self.tag)
        self.definition["pfcand_dEdx_wires_type{}".format(self.tag)] = "AlephSelection::get_dEdx_type(jet_constituents_dEdx_wires_objs{})".format(self.tag)
        self.definition["pfcand_dEdx_wires_value{}".format(self.tag)] = "AlephSelection::get_dEdx_value(jet_constituents_dEdx_wires_objs{})".format(self.tag)
        self.definition["pfcand_dEdx_wires_error{}".format(self.tag)] = "AlephSelection::get_dEdx_error(jet_constituents_dEdx_wires_objs{})".format(self.tag)
        self.definition["jet_constituents_PID_pvals_wires{}".format(self.tag)] = "jet_constituents_dEdx_PIDhypo_wires_result{}.pid_array_constituents".format(self.tag)
        self.definition["pfcand_PID_pval_wires_ele{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_wires{}, 0)".format(self.tag)
        self.definition["pfcand_PID_pval_wires_mu{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_wires{}, 1)".format(self.tag)
        self.definition["pfcand_PID_pval_wires_pi{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_wires{}, 2)".format(self.tag)
        self.definition["pfcand_PID_pval_wires_kaon{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_wires{}, 3)".format(self.tag)
        self.definition["pfcand_PID_pval_wires_proton{}".format(self.tag)] = "AlephSelection::get_PID_pvalue(jet_constituents_PID_pvals_wires{}, 4)".format(self.tag)

        # ===== JET COUNTS
        self.definition["jet_nmu{}".format(self.tag)] = "JetConstituentsUtils::count_type(pfcand_isMu{})".format(self.tag)
        self.definition["jet_nel{}".format(self.tag)] = "JetConstituentsUtils::count_type(pfcand_isEl{})".format(self.tag)
        self.definition["jet_nchad{}".format(self.tag)] = "JetConstituentsUtils::count_type(pfcand_isChargedHad{})".format(self.tag)
        self.definition["jet_ngamma{}".format(self.tag)] = "JetConstituentsUtils::count_type(pfcand_isGamma{})".format(self.tag)
        self.definition["jet_nnhad{}".format(self.tag)] = "JetConstituentsUtils::count_type(pfcand_isNeutralHad{})".format(self.tag)

    def define(self, df):
        for var, call in self.definition.items():
            df = df.Define(var, call)
        return df

    def inference(self, jsonCfg, onnxCfg, df):

        initvars, self.variables, self.scores = [], [], []
        f = open(jsonCfg)
        data = json.load(f)

        for varname in data["pf_features"]["var_names"]:
            initvars.append(varname)
            self.variables.append("{}{}".format(varname, self.tag))

        for varname in data["pf_vectors"]["var_names"]:
            initvars.append(varname)
            self.variables.append("{}{}".format(varname, self.tag))

        for varname in data["pf_mask"]["var_names"]:
            initvars.append(varname)
            self.variables.append("{}{}".format(varname, self.tag))

        for scorename in data["output_names"]:
            self.scores.append("{}{}".format(scorename, self.tag))

        f.close()
        initvars = tuple(initvars)

        for varname in self.variables:
            matches = [obs for obs in self.definition.keys() if obs == varname]
            if len(matches) != 1:
                print("ERROR: {} variables was not defined.".format(varname))
                sys.exit()

        self.get_weight_str = "JetFlavourUtils::get_weights(rdfslot_, "
        for var in self.variables:
            self.get_weight_str += "{},".format(var)
        self.get_weight_str = "{})".format(self.get_weight_str[:-1])

        from ROOT import JetFlavourUtils

        weaver = JetFlavourUtils.setup_weaver(
            onnxCfg,
            jsonCfg,
            initvars,
            ROOT.GetThreadPoolSize() if ROOT.GetThreadPoolSize() > 0 else 1,
        )

        df = df.Define("MVAVec_{}".format(self.tag), self.get_weight_str)

        for i, scorename in enumerate(self.scores):
            df = df.Define(scorename, "JetFlavourUtils::get_weight(MVAVec_{}, {})".format(self.tag, i))

        return df

    def outputBranches(self):
        out = list(self.scores) if hasattr(self, 'scores') else []
        
        # Exclude intermediate result columns that can't be written to disk
        exclude_patterns = [
            "jet_constituents_dEdx_PIDhypo_pads_result",
            "jet_constituents_dEdx_PIDhypo_wires_result",
            "jet_constituents_dEdx_pads_objs",
            "jet_constituents_dEdx_wires_objs",
            "jet_constituents_PID_pvals_pads",
            "jet_constituents_PID_pvals_wires",
        ]
        
        out += [
            obs for obs in self.definition.keys()
            if "jet_" in obs and obs not in exclude_patterns
        ]
        return out
