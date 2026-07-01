import 'dart:developer' as developer;
import 'dart:io';

import 'package:collection/collection.dart';
import 'package:tflite_flutter/tflite_flutter.dart';

import '../config/app_config.dart';
import '../models/prediction_result.dart';
import '../models/sign_mode.dart';
import 'label_service.dart';

class TfliteSignClassifier {
  TfliteSignClassifier({
    required this.metadata,
    this.preferDynamicRangeModel = AppConfig.preferDynamicRangeModel,
  });

  final LabelMetadata metadata;
  final bool preferDynamicRangeModel;

  Interpreter? _interpreter;
  String? _modelAsset;

  bool get isLoaded => _interpreter != null;

  String get selectedModelAsset {
    return _modelAsset ??
        (preferDynamicRangeModel
            ? AppConfig.dynamicRangeModelAsset
            : AppConfig.float32ModelAsset);
  }

  Future<void> load() async {
    final asset = preferDynamicRangeModel
        ? AppConfig.dynamicRangeModelAsset
        : AppConfig.float32ModelAsset;
    try {
      _validateWindowsRuntimeIfNeeded();
      _interpreter = await Interpreter.fromAsset(asset);
      _modelAsset = asset;
      _validateTensorShapes();
      developer.log('TFLite model loaded: $asset');
    } catch (error, stackTrace) {
      developer.log(
        'TFLite model loading failed',
        error: error,
        stackTrace: stackTrace,
      );
      throw StateError(_formatLoadError(error));
    }
  }

  PredictionResult predict(List<double> features, SignMode mode) {
    final interpreter = _interpreter;
    if (interpreter == null) {
      throw StateError('TFLite model is not loaded.');
    }
    if (features.length != AppConfig.expectedInputWidth) {
      throw ArgumentError('Expected 756 features, found ${features.length}.');
    }

    final input = <List<double>>[features];
    final output = List<List<double>>.generate(
      1,
      (_) => List<double>.filled(AppConfig.expectedOutputClasses, 0),
      growable: false,
    );

    interpreter.run(input, output);
    final probabilities = output.first;
    if (probabilities.length != AppConfig.expectedOutputClasses) {
      throw StateError(
        'Expected 86 output probabilities, found ${probabilities.length}.',
      );
    }

    final selectedIndices = _indicesForMode(mode);
    final topPredictions = _topPredictions(probabilities, selectedIndices);
    final rawTopPredictions = _topPredictions(
      probabilities,
      List<int>.generate(probabilities.length, (index) => index),
    );

    return PredictionResult(
      predictedLabel: topPredictions.first.label,
      confidence: topPredictions.first.probability,
      topPredictions: topPredictions,
      rawTopPredictions: rawTopPredictions,
      rawOutputLength: probabilities.length,
      selectedMode: mode,
      modelAsset: selectedModelAsset,
    );
  }

  void close() {
    _interpreter?.close();
    _interpreter = null;
  }

  void _validateTensorShapes() {
    final interpreter = _interpreter;
    if (interpreter == null) {
      throw StateError('TFLite model is not loaded.');
    }

    final inputShape = interpreter.getInputTensor(0).shape;
    final outputShape = interpreter.getOutputTensor(0).shape;
    if (!const ListEquality<int>().equals(inputShape, const [
      1,
      AppConfig.expectedInputWidth,
    ])) {
      throw StateError(
        'Expected TFLite input shape [1, 756], found $inputShape.',
      );
    }
    if (!const ListEquality<int>().equals(outputShape, const [
      1,
      AppConfig.expectedOutputClasses,
    ])) {
      throw StateError(
        'Expected TFLite output shape [1, 86], found $outputShape.',
      );
    }
  }

  void _validateWindowsRuntimeIfNeeded() {
    if (!Platform.isWindows) {
      return;
    }

    final dllFile = File(_windowsRuntimeDllPath);
    if (!dllFile.existsSync()) {
      throw StateError(
        'Windows desktop requires the TensorFlow Lite C runtime DLL. '
        'Add libtensorflowlite_c-win.dll to flutter_app/blobs, then rerun '
        'flutter run -d windows. Expected runtime copy path: $_windowsRuntimeDllPath. '
        'Android/mobile remains the main Sprint 2.14 target.',
      );
    }
  }

  String get _windowsRuntimeDllPath {
    return '${File(Platform.resolvedExecutable).parent.path}'
        '${Platform.pathSeparator}blobs'
        '${Platform.pathSeparator}libtensorflowlite_c-win.dll';
  }

  String _formatLoadError(Object error) {
    if (Platform.isWindows) {
      return 'TFLite Windows runtime could not be loaded. Ensure '
          'flutter_app/blobs/libtensorflowlite_c-win.dll is present and that '
          'the Microsoft Visual C++ Redistributable is installed. Details: $error';
    }
    return error.toString();
  }

  List<int> _indicesForMode(SignMode mode) {
    return metadata.indicesForMode(mode);
  }

  List<TopPrediction> _topPredictions(
    List<double> probabilities,
    List<int> indices,
  ) {
    final predictions =
        indices.map((index) {
          return TopPrediction(
            label: metadata.labels[index],
            probability: probabilities[index],
            index: index,
          );
        }).toList()..sort(
          (left, right) => right.probability.compareTo(left.probability),
        );

    return predictions.take(5).toList(growable: false);
  }
}
