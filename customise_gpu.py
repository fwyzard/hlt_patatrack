import FWCore.ParameterSet.Config as cms

# customisation for offloading to GPUs, common parts
def customise_gpu_common(process):

    # Services

    process.CUDAService = cms.Service("CUDAService",
        allocator = cms.untracked.PSet(
            binGrowth = cms.untracked.uint32(8),
            debug = cms.untracked.bool(False),
            devicePreallocate = cms.untracked.vuint32(),
            enabled = cms.untracked.bool(True),
            hostPreallocate = cms.untracked.vuint32(),
            maxBin = cms.untracked.uint32(9),
            maxCachedBytes = cms.untracked.uint32(0),
            maxCachedFraction = cms.untracked.double(0.8),
            minBin = cms.untracked.uint32(1)
        ),
        enabled = cms.untracked.bool(True),
        limits = cms.untracked.PSet(
            cudaLimitDevRuntimePendingLaunchCount = cms.untracked.int32(-1),
            cudaLimitDevRuntimeSyncDepth = cms.untracked.int32(-1),
            cudaLimitMallocHeapSize = cms.untracked.int32(-1),
            cudaLimitPrintfFifoSize = cms.untracked.int32(-1),
            cudaLimitStackSize = cms.untracked.int32(-1)
        )
    )

    process.load('HeterogeneousCore.CUDAServices.NVProfilerService_cfi')

    # done
    return process


# customisation for offloading the Pixel local reconstruction to GPUs
def customise_gpu_pixel(process):

    # FIXME replace the Sequences with empty ones to avoid exanding them during the (re)definition of Modules and EDAliases

    process.HLTDoLocalPixelSequence = cms.Sequence()
    process.HLTRecoPixelTracksSequence = cms.Sequence()
    #process.HLTRecopixelvertexingSequence is unchanged


    # Event Setup

    process.siPixelGainCalibrationForHLTGPU = cms.ESProducer("SiPixelGainCalibrationForHLTGPUESProducer",
        appendToDataLabel = cms.string('')
    )

    process.siPixelFedCablingMapGPUWrapper = cms.ESProducer("SiPixelFedCablingMapGPUWrapperESProducer",
        CablingMapLabel = cms.string(''),
        ComponentName = cms.string(''),
        UseQualityInfo = cms.bool(False),
        appendToDataLabel = cms.string('')
    )

    process.PixelCPEFastESProducer = cms.ESProducer("PixelCPEFastESProducer",
        Alpha2Order = cms.bool(True),
        ClusterProbComputationFlag = cms.int32(0),
        ComponentName = cms.string('PixelCPEFast'),
        EdgeClusterErrorX = cms.double(50.0),
        EdgeClusterErrorY = cms.double(85.0),
        LoadTemplatesFromDB = cms.bool(True),
        MagneticFieldRecord = cms.ESInputTag(""),
        TruncatePixelCharge = cms.bool(True),
        UseErrorsFromTemplates = cms.bool(True),
        useLAAlignmentOffsets = cms.bool(False),
        useLAWidthFromDB = cms.bool(True)
    )


    # Modules and EDAliases

    # referenced in process.HLTDoLocalPixelSequence
    process.hltOnlineBeamSpotCUDA = cms.EDProducer("BeamSpotToCUDA",
        src = cms.InputTag("hltOnlineBeamSpot")
    )

    process.siPixelClustersCUDAPreSplitting = cms.EDProducer("SiPixelRawToClusterCUDA",
        CablingMapLabel = cms.string(''),
        IncludeErrors = cms.bool(True),
        InputLabel = cms.InputTag("rawDataCollector"),
        Regions = cms.PSet(
        ),
        UsePilotBlade = cms.bool(False),
        UseQualityInfo = cms.bool(False)
    )

    process.siPixelRecHitsCUDAPreSplitting = cms.EDProducer("SiPixelRecHitCUDA",
        CPE = cms.string('PixelCPEFast'),
        beamSpot = cms.InputTag("hltOnlineBeamSpotCUDA"),
        src = cms.InputTag("siPixelClustersCUDAPreSplitting")
    )

    process.siPixelDigisSoA = cms.EDProducer("SiPixelDigisSoAFromCUDA",
        src = cms.InputTag("siPixelClustersCUDAPreSplitting")
    )

    process.siPixelDigisClustersPreSplitting = cms.EDProducer("SiPixelDigisClustersFromSoA",
        src = cms.InputTag("siPixelDigisSoA")
    )

    process.siPixelDigiErrorsSoA = cms.EDProducer("SiPixelDigiErrorsSoAFromCUDA",
        src = cms.InputTag("siPixelClustersCUDAPreSplitting")
    )

    process.siPixelDigiErrors = cms.EDProducer("SiPixelDigiErrorsFromSoA",
        CablingMapLabel = cms.string(''),
        ErrorList = cms.vint32(29),
        UsePhase1 = cms.bool(True),
        UserErrorList = cms.vint32(40),
        digiErrorSoASrc = cms.InputTag("siPixelDigiErrorsSoA")
    )

    process.hltSiPixelRecHits = cms.EDProducer("SiPixelRecHitFromSOA",
        pixelRecHitSrc = cms.InputTag("siPixelRecHitsCUDAPreSplitting"),
        src = cms.InputTag("siPixelDigisClustersPreSplitting")
    )

    process.hltSiPixelDigis = cms.EDAlias(
        siPixelDigisClustersPreSplitting = cms.VPSet(
            cms.PSet(
                type = cms.string('PixelDigiedmDetSetVector')
            )
        ),
        siPixelDigiErrors = cms.VPSet(
            cms.PSet(
                type = cms.string('DetIdedmEDCollection')
            ),
            cms.PSet(
                type = cms.string('SiPixelRawDataErroredmDetSetVector')
            ),
            cms.PSet(
                type = cms.string('PixelFEDChanneledmNewDetSetVector')
            )
        )
    )

    process.hltSiPixelClusters = cms.EDAlias(
        siPixelDigisClustersPreSplitting = cms.VPSet(
            cms.PSet(
                type = cms.string('SiPixelClusteredmNewDetSetVector')
            )
        )
    )

    # referenced in process.HLTRecoPixelTracksSequence
    process.hltPixelTracksHitQuadruplets = cms.EDProducer("CAHitNtupletHeterogeneousEDProducer",
        heterogeneousEnabled_ = cms.untracked.PSet(
            GPUCuda = cms.untracked.bool(True),
            force = cms.untracked.string('')
        ),
        gpuEnableTransfer = cms.bool(True),
        gpuEnableConversion = cms.bool(True),
        CAHardPtCut = cms.double(0),
        CAPhiCut = cms.double(10),
        CAThetaCut = cms.double(0.00125),
        CAThetaCutBarrel = cms.double(0.00200000009499),
        CAThetaCutForward = cms.double(0.00300000002608),
        dcaCutInnerTriplet = cms.double(0.15000000596),
        dcaCutOuterTriplet = cms.double(0.25),
        doClusterCut = cms.bool(True),
        doPhiCut = cms.bool(True),
        doZCut = cms.bool(True),
        earlyFishbone = cms.bool(False),
        fillStatistics = cms.bool(False),
        fit5as4 = cms.bool(True),
        hardCurvCut = cms.double(0.0328407224959),
        idealConditions = cms.bool(True),
        lateFishbone = cms.bool(True),
        minHitsPerNtuplet = cms.uint32(4),
        pixelRecHitLegacySrc = cms.InputTag("hltSiPixelRecHits"),
        pixelRecHitSrc = cms.InputTag("siPixelRecHitsCUDAPreSplitting"),
        ptmin = cms.double(0.899999976158),
        trackingRegions = cms.InputTag("hltPixelTracksTrackingRegions"),
        useRiemannFit = cms.bool(False)
    )

    process.hltPixelTracks = cms.EDProducer("PixelTrackProducerFromCUDA",
        heterogeneousEnabled_ = cms.untracked.PSet(
            GPUCuda = cms.untracked.bool(True),
            force = cms.untracked.string('')
        ),
        gpuEnableConversion = cms.bool(True),
        beamSpot = cms.InputTag("hltOnlineBeamSpot"),
        src = cms.InputTag("hltPixelTracksHitQuadruplets")
    )

    # referenced in process.HLTRecopixelvertexingSequence
    process.hltPixelVertices = cms.EDProducer("PixelVertexHeterogeneousProducer",
        heterogeneousEnabled_ = cms.untracked.PSet(
            GPUCuda = cms.untracked.bool(True),
            force = cms.untracked.string('')
        ),
        gpuEnableTransfer = cms.bool(True),
        gpuEnableConversion = cms.bool(True),
        PtMin = cms.double(0.5),
        TrackCollection = cms.InputTag("hltPixelTracks"),
        beamSpot = cms.InputTag("hltOnlineBeamSpot"),
        chi2max = cms.double(9),
        eps = cms.double(0.07),
        errmax = cms.double(0.01),
        minT = cms.int32(2),
        src = cms.InputTag("hltPixelTracksHitQuadruplets"),
        useDBSCAN = cms.bool(False),
        useDensity = cms.bool(True),
        useIterative = cms.bool(False)
    )


    # Sequences

    process.HLTDoLocalPixelSequence = cms.Sequence(
          process.hltOnlineBeamSpotCUDA                     # transfer the beamspot to the gpu
        + process.siPixelClustersCUDAPreSplitting           # digis and clusters on gpu
        + process.siPixelRecHitsCUDAPreSplitting            # rechits on gpu
        + process.siPixelDigisSoA                           # copy to host
        + process.siPixelDigisClustersPreSplitting          # convert to legacy
        + process.siPixelDigiErrorsSoA                      # copy to host
        + process.siPixelDigiErrors                         # convert to legacy
        # process.hltSiPixelDigis                           # replaced by an alias
        # process.hltSiPixelClusters                        # replaced by an alias
        + process.hltSiPixelClustersCache                   # not used here, kept for compatibility with legacy sequences
        + process.hltSiPixelRecHits)                        # convert to legacy

    process.HLTRecoPixelTracksSequence = cms.Sequence(
          process.hltPixelTracksFitter                      # not used here, kept for compatibility with legacy sequences
        + process.hltPixelTracksFilter                      # not used here, kept for compatibility with legacy sequences
        + process.hltPixelTracksTrackingRegions             #
        + process.hltPixelTracksHitQuadruplets              # pixel ntuplets on gpu, with transfer and conversion to legacy
        + process.hltPixelTracks)                           # pixel tracks on gpu, with transfer and conversion to legacy

    #process.HLTRecopixelvertexingSequence is unchanged


    # done
    return process


# customisation for offloading the ECAL local reconstruction to GPUs
# TODO find automatically the list of Sequences to be updated
def customise_gpu_ecal(process):

    # FIXME replace the Sequences with empty ones to avoid exanding them during the (re)definition of Modules and EDAliases

    process.HLTDoFullUnpackingEgammaEcalMFSequence = cms.Sequence()
    process.HLTDoFullUnpackingEgammaEcalWithoutPreshowerSequence = cms.Sequence()
    process.HLTDoFullUnpackingEgammaEcalSequence = cms.Sequence()


    # Event Setup

    process.load("RecoLocalCalo.EcalRecProducers.ecalGainRatiosGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalPedestalsGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalPulseCovariancesGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalPulseShapesGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalSamplesCorrelationGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalTimeBiasCorrectionsGPUESProducer_cfi")
    process.load("RecoLocalCalo.EcalRecProducers.ecalTimeCalibConstantsGPUESProducer_cfi")


    # Modules and EDAliases

    process.hltEcalUncalibRecHitSoA = cms.EDProducer("EcalUncalibRecHitProducerGPU",
        digisLabelEB = cms.InputTag("hltEcalDigis","ebDigis"),
        recHitsLabelEB = cms.string('EcalUncalibRecHitsEB'),
        digisLabelEE = cms.InputTag("hltEcalDigis","eeDigis"),
        recHitsLabelEE = cms.string('EcalUncalibRecHitsEE'),
        EBamplitudeFitParameters = cms.vdouble(1.138, 1.652),
        EBtimeConstantTerm = cms.double(0.6),
        EBtimeFitLimits_Lower = cms.double(0.2),
        EBtimeFitLimits_Upper = cms.double(1.4),
        EBtimeFitParameters = cms.vdouble(-2.015452, 3.130702, -12.3473, 41.88921, -82.83944, 91.01147, -50.35761, 11.05621),
        EBtimeNconst = cms.double(28.5),
        EEamplitudeFitParameters = cms.vdouble(1.89, 1.4),
        EEtimeConstantTerm = cms.double(1.0),
        EEtimeFitLimits_Lower = cms.double(0.2),
        EEtimeFitLimits_Upper = cms.double(1.4),
        EEtimeFitParameters = cms.vdouble(-2.390548, 3.553628, -17.62341, 67.67538, -133.213, 140.7432, -75.41106, 16.20277),
        EEtimeNconst = cms.double(31.8),
        amplitudeThresholdEB = cms.double(10.0),
        amplitudeThresholdEE = cms.double(10.0),
        outOfTimeThresholdGain12mEB = cms.double(5.0),
        outOfTimeThresholdGain12mEE = cms.double(1000.0),
        outOfTimeThresholdGain12pEB = cms.double(5.0),
        outOfTimeThresholdGain12pEE = cms.double(1000.0),
        outOfTimeThresholdGain61mEB = cms.double(5.0),
        outOfTimeThresholdGain61mEE = cms.double(1000.0),
        outOfTimeThresholdGain61pEB = cms.double(5.0),
        outOfTimeThresholdGain61pEE = cms.double(1000.0),
        kernelMinimizeThreads = cms.vuint32(32, 1, 1),
        maxNumberHits = cms.uint32(20000),
        shouldRunTimingComputation = cms.bool(False),
        shouldTransferToHost = cms.bool(True)
    )

    process.hltEcalUncalibRecHit = cms.EDProducer('EcalUncalibRecHitConvertGPU2CPUFormat',
        recHitsLabelGPUEB = cms.InputTag('hltEcalUncalibRecHitSoA', 'EcalUncalibRecHitsEB'),
        recHitsLabelGPUEE = cms.InputTag('hltEcalUncalibRecHitSoA', 'EcalUncalibRecHitsEE'),
        recHitsLabelCPUEB = cms.string('EcalUncalibRecHitsEB'),
        recHitsLabelCPUEE = cms.string('EcalUncalibRecHitsEE')
    )


    # Sequences

    process.HLTDoFullUnpackingEgammaEcalMFSequence = cms.Sequence(
        process.hltEcalDigis
      + process.hltEcalPreshowerDigis
      + process.hltEcalUncalibRecHitSoA
      + process.hltEcalUncalibRecHit
      + process.hltEcalDetIdToBeRecovered
      + process.hltEcalRecHit
      + process.hltEcalPreshowerRecHit)

    process.HLTDoFullUnpackingEgammaEcalWithoutPreshowerSequence = cms.Sequence(
        process.hltEcalDigis
      + process.hltEcalUncalibRecHitSoA
      + process.hltEcalUncalibRecHit
      + process.hltEcalDetIdToBeRecovered
      + process.hltEcalRecHit)

    process.HLTDoFullUnpackingEgammaEcalSequence = cms.Sequence(
        process.hltEcalDigis
      + process.hltEcalPreshowerDigis
      + process.hltEcalUncalibRecHitSoA
      + process.hltEcalUncalibRecHit
      + process.hltEcalDetIdToBeRecovered
      + process.hltEcalRecHit
      + process.hltEcalPreshowerRecHit)


    # done
    return process


# customisation for offloading to GPUs
def customise_gpu(process):
    process = customise_gpu_common(process)
    process = customise_gpu_pixel(process)
    process = customise_gpu_ecal(process)
    return process
