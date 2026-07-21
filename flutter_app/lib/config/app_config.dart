class AppConfig {
  static const String appTitle = 'SignSync';
  static const String appSubtitle =
      'Private, on-device banking communication assistance.';

  static const String dynamicRangeModelAsset =
      'assets/models/signsync_40class_account_corrected_v2_dynamic_range.tflite';
  static const String float32ModelAsset =
      'assets/models/signsync_40class_account_corrected_v2_float32.tflite';
  static const String labelsAsset = 'assets/models/labels_40.json';
  static const String modelMetadataAsset =
      'assets/models/model_metadata_40class.json';
  static const String featureContractAsset =
      'assets/models/feature_contract_40class.json';
  static const String confidenceRecommendationAsset =
      'assets/models/confidence_recommendation_40class.json';
  static const String deploymentManifestAsset =
      'assets/models/model_deployment_manifest.json';
  static const String testFeatureAssetFolder = 'assets/test_features';
  static const String bankingQueriesAsset =
      'assets/content/banking_queries.json';

  static const bool preferDynamicRangeModel = true;
  static const int expectedInputWidth = 756;
  static const int expectedOutputClasses = 40;
  static const int expectedFrameCount = 60;
  static const int expectedFrameWidth = 126;
  static const int expectedBankingIntentModeLabels = 40;
  static const int expectedRemovedBankingIntents = 10;

  static const double bankingIntentConfidenceThreshold = 0.80;
  static const double minimumTop2Gap = 0.00;
  static const bool bankingOnlyRecognition = true;
  static const String modelVersion = 'signsync_40class_account_corrected_v2';
  static const String deploymentStatus =
      'deployed_for_account_savings_a55_verification';
  static const String androidPackageId = 'com.example.flutter_app';
  static const String iosBundleId = 'com.example.flutterApp';
  static const int stabilizedCaptureCount = 3;
  static const int stabilizedAgreementCount = 2;

  static const String evaluationProtocolVersion =
      'sprint_2_19_live_evaluation_v1';
  static const String evaluationScheduleAsset =
      'assets/evaluation/sprint_2_19_trial_schedule.csv';
  static const int evaluationRandomSeed = 21919;
  static const int evaluationTrialCount = 400;
  static const int evaluationWarmUpCount = 5;
  static const String evaluationScheduleSha256 =
      '57E858AB6D6AB0C978BAD3E6A73EB2E08BC7531CE5F766AD82953B3FA558CB76';
  static const String activeDynamicModelSha256 =
      'BD46131FF20ECB96F240C867C60804A2D9F514AC4F56D63F64E8B60188187A17';
  static const String activeLabelsSha256 =
      'CF8BE5AD57C57A3EDA1029010FA7A5D9663F226294661A869CED375E0236E286';
  static const String deploymentManifestSha256 =
      'F02E35864C87925A6D06D70F669411388B2F04112F757CB0DF2AAD1296A2F9F1';
}
