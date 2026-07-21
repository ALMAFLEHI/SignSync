import 'dart:developer' as developer;
import 'dart:io';

import 'package:collection/collection.dart';
import 'package:tflite_flutter/tflite_flutter.dart';

import '../config/app_config.dart';
import '../models/prediction_result.dart';
import '../models/sign_mode.dart';
import 'final_model_runtime_diagnostics.dart';
import 'label_service.dart';
import 'prediction_decision_policy.dart';

class TfliteSignClassifier {
  TfliteSignClassifier({
    required this.metadata,
    this.preferDynamicRangeModel = AppConfig.preferDynamicRangeModel,
    this.decisionPolicy = const PredictionDecisionPolicy(),
  });

  final LabelMetadata metadata;
  final bool preferDynamicRangeModel;
  final PredictionDecisionPolicy decisionPolicy;

  Interpreter? _interpreter;
  String? _modelAsset;
  bool _contractValidated = false;
  String? _diagnosticError;

  bool get isLoaded => _interpreter != null;
  bool get contractValidated => _contractValidated;
  String? get diagnosticError => _diagnosticError;

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
      final loadWatch = Stopwatch()..start();
      _validateWindowsRuntimeIfNeeded();
      _interpreter = await Interpreter.fromAsset(asset);
      _modelAsset = asset;
      _validateTensorContract();
      loadWatch.stop();
      FinalModelRuntimeDiagnostics.recordModelLoad(loadWatch.elapsed);
      _contractValidated = true;
      _diagnosticError = null;
      developer.log('TFLite model loaded: $asset');
    } catch (error, stackTrace) {
      _interpreter?.close();
      _interpreter = null;
      _modelAsset = null;
      _contractValidated = false;
      _diagnosticError = error.toString();
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
    if (!mode.isActiveForFinalModel) {
      throw UnsupportedError(
        'Historical Alphabet and Number modes cannot use the final 40-class model.',
      );
    }
    if (features.any((value) => !value.isFinite)) {
      throw ArgumentError('Feature vector contains a non-finite value.');
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
        'Expected ${AppConfig.expectedOutputClasses} output probabilities, '
        'found ${probabilities.length}.',
      );
    }
    if (probabilities.any((value) => !value.isFinite)) {
      throw StateError('TFLite inference produced a non-finite probability.');
    }
    if (probabilities.any((value) => value < 0 || value > 1)) {
      throw StateError('TFLite inference produced an invalid probability.');
    }

    final selectedIndices = _indicesForMode(mode);
    final topPredictions = _topPredictions(probabilities, selectedIndices);
    final decision = decisionPolicy.decide(
      filteredTopPredictions: topPredictions,
      mode: mode,
    );
    final rawTopPredictions = _topPredictions(
      probabilities,
      List<int>.generate(probabilities.length, (index) => index),
    );

    return PredictionResult(
      predictedLabel: topPredictions.first.label,
      confidence: topPredictions.first.probability,
      decision: decision,
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
    _contractValidated = false;
  }

  void _validateTensorContract() {
    final interpreter = _interpreter;
    if (interpreter == null) {
      throw StateError('TFLite model is not loaded.');
    }

    final inputTensors = interpreter.getInputTensors();
    final outputTensors = interpreter.getOutputTensors();
    if (inputTensors.length != 1 || outputTensors.length != 1) {
      throw StateError(
        'Expected one input and one output tensor, found '
        '${inputTensors.length} and ${outputTensors.length}.',
      );
    }
    final inputTensor = inputTensors.single;
    final outputTensor = outputTensors.single;
    final inputShape = inputTensor.shape;
    final outputShape = outputTensor.shape;
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
        'Expected TFLite output shape '
        '[1, ${AppConfig.expectedOutputClasses}], found $outputShape.',
      );
    }
    if (inputTensor.type != TensorType.float32 ||
        outputTensor.type != TensorType.float32) {
      throw StateError(
        'Expected float32 TFLite I/O, found '
        '${inputTensor.type} and ${outputTensor.type}.',
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
    if (!mode.isActiveForFinalModel) {
      throw UnsupportedError(
        'Historical recognition mode is unavailable with the final model.',
      );
    }
    return metadata.indicesForMode(mode);
  }

  List<TopPrediction> _topPredictions(
    List<double> probabilities,
    List<int> indices,
  ) {
    if (indices.isEmpty ||
        indices.any((index) => index < 0 || index >= metadata.labels.length)) {
      throw StateError('Prediction indices do not match the final label set.');
    }
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
