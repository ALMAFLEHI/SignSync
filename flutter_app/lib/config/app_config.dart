class AppConfig {
  static const String appTitle = 'SignSync';
  static const String appSubtitle = 'On-device ASL-to-text banking prototype';

  static const String dynamicRangeModelAsset =
      'assets/models/model_dynamic_range.tflite';
  static const String float32ModelAsset = 'assets/models/model_float32.tflite';
  static const String labelsAsset = 'assets/metadata/labels.txt';
  static const String labelMappingAsset = 'assets/metadata/label_mapping.json';
  static const String labelGroupsAsset = 'assets/metadata/label_groups.json';
  static const String modelMetadataAsset =
      'assets/metadata/tflite_model_metadata.json';
  static const String testFeatureAssetFolder = 'assets/test_features';

  static const bool preferDynamicRangeModel = true;
  static const int expectedInputWidth = 756;
  static const int expectedOutputClasses = 86;
  static const int expectedFrameCount = 60;
  static const int expectedFrameWidth = 126;
  static const int expectedNormalModeLabels = 76;
  static const int expectedNumberModeLabels = 10;
}
