import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

import '../config/app_config.dart';
import '../models/live_landmark_frame.dart';
import '../models/live_prediction_session.dart';
import '../models/prediction_result.dart';
import '../models/sign_mode.dart';
import '../services/label_service.dart';
import '../services/banking_prediction_gate.dart';
import '../services/live_landmark_service.dart';
import '../services/live_recognition_service.dart';
import '../services/tflite_sign_classifier.dart';
import 'widgets/top_predictions_list.dart';

typedef LiveTechnicalErrorCallback =
    void Function(String eventType, String message);

class LiveCameraPage extends StatefulWidget {
  const LiveCameraPage({
    super.key,
    this.bankingOnly = true,
    this.embedded = false,
    this.onPrediction,
    this.onSession,
    this.onTechnicalError,
    this.onCaptureReset,
    this.onCancel,
    this.captureLocked = false,
    this.allowTryAgain = true,
    this.lockAfterSession = false,
    this.captureCycleToken,
  });

  final bool bankingOnly;
  final bool embedded;
  final ValueChanged<PredictionResult>? onPrediction;
  final ValueChanged<LivePredictionSession>? onSession;
  final LiveTechnicalErrorCallback? onTechnicalError;
  final VoidCallback? onCaptureReset;
  final VoidCallback? onCancel;
  final bool captureLocked;
  final bool allowTryAgain;
  final bool lockAfterSession;
  final Object? captureCycleToken;

  @override
  State<LiveCameraPage> createState() => _LiveCameraPageState();
}

class _LiveCameraPageState extends State<LiveCameraPage> {
  final LabelService _labelService = LabelService();
  late final LiveLandmarkService _landmarkService;

  TfliteSignClassifier? _classifier;
  LiveRecognitionService? _recognitionService;
  LiveLandmarkFrame? _lastFrame;
  LivePredictionSession? _session;

  String _statusMessage = 'Loading live camera prototype assets...';
  String? _errorMessage;
  bool _isLoading = true;
  bool _isCameraStarting = false;
  bool _isCameraStarted = false;
  bool _isCapturing = false;
  bool _isPredicting = false;
  int _validFrameCount = 0;

  bool get _showDeveloperDetails => !widget.embedded;

  @override
  void initState() {
    super.initState();
    _statusMessage = 'Preparing the final 40-class on-device model...';
    _landmarkService = LiveLandmarkService()
      ..onStatus = _handleStatus
      ..onError = _handleError
      ..onFrame = _handleLiveFrame
      ..onCaptureProgress = _handleCaptureProgress
      ..onCaptureComplete = _handleCaptureComplete;
    _initialize();
  }

  @override
  void didUpdateWidget(covariant LiveCameraPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.captureCycleToken != widget.captureCycleToken) {
      _session = null;
      _validFrameCount = 0;
    }
  }

  @override
  void dispose() {
    _classifier?.close();
    unawaited(_landmarkService.dispose());
    super.dispose();
  }

  Future<void> _initialize() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _statusMessage = 'Preparing the final 40-class on-device model...';
    });

    try {
      final metadata = await _labelService.load();
      final classifier = TfliteSignClassifier(metadata: metadata);
      await classifier.load();

      if (!mounted) {
        classifier.close();
        return;
      }

      setState(() {
        _classifier = classifier;
        _recognitionService = LiveRecognitionService(classifier: classifier);
        _isLoading = false;
        _statusMessage =
            'Ready. Start the camera and perform one banking intent sign.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _isLoading = false;
        _errorMessage = _showDeveloperDetails
            ? error.toString()
            : 'On-device recognition could not be prepared.';
        _statusMessage = 'Live camera setup could not finish.';
      });
      widget.onTechnicalError?.call('model_load_failure', error.toString());
    }
  }

  Future<void> _startCamera() async {
    if (!Platform.isAndroid) {
      setState(() {
        _errorMessage = 'Live camera capture is supported on Android only.';
      });
      return;
    }

    setState(() {
      _isCameraStarting = true;
      _errorMessage = null;
      _statusMessage = 'Requesting camera permission...';
    });

    final permission = await Permission.camera.request();
    if (!mounted) {
      return;
    }
    if (!permission.isGranted) {
      setState(() {
        _isCameraStarting = false;
        _errorMessage = 'Camera permission was denied.';
        _statusMessage = 'Grant camera permission to use live recognition.';
      });
      widget.onTechnicalError?.call(
        'camera_permission_issue',
        'Camera permission was denied.',
      );
      return;
    }

    try {
      await _landmarkService.startCamera();
      if (!mounted) {
        return;
      }
      setState(() {
        _isCameraStarted = true;
        _isCameraStarting = false;
        _statusMessage = 'Camera started. Present a hand sign in view.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _isCameraStarting = false;
        _errorMessage = _showDeveloperDetails
            ? error.toString()
            : 'The camera could not start. Check permission and try again.';
        _statusMessage = 'Camera could not start.';
      });
    }
  }

  Future<void> _stopCamera() async {
    await _landmarkService.stopCamera();
    if (!mounted) {
      return;
    }
    setState(() {
      _isCameraStarted = false;
      _isCapturing = false;
      _statusMessage = 'Camera stopped.';
    });
  }

  Future<void> _startCapture() async {
    if (_classifier == null || _recognitionService == null) {
      setState(() {
        _errorMessage = 'TFLite model is not loaded yet.';
      });
      return;
    }
    if (!_isCameraStarted) {
      setState(() {
        _errorMessage = 'Start the Android camera before capturing frames.';
      });
      return;
    }

    setState(() {
      _validFrameCount = 0;
      _session = null;
      _isCapturing = true;
      _isPredicting = false;
      _errorMessage = null;
      _statusMessage = 'Capturing 60 valid frames for one banking sign...';
    });
    await _landmarkService.startCapture();
  }

  Future<void> _resetCapture() async {
    final wasCapturing = _isCapturing;
    await _landmarkService.resetCapture();
    if (!mounted) {
      return;
    }
    setState(() {
      _validFrameCount = 0;
      _isCapturing = false;
      _isPredicting = false;
      _session = null;
      _errorMessage = null;
      _statusMessage = 'Capture buffer reset.';
    });
    if (wasCapturing) {
      widget.onCaptureReset?.call();
    }
  }

  void _handleStatus(String message) {
    if (!mounted || message.isEmpty) {
      return;
    }
    setState(() {
      _statusMessage = message;
    });
  }

  void _handleError(String message) {
    if (!mounted) {
      return;
    }
    setState(() {
      _errorMessage = message.isEmpty ? 'Live camera error.' : message;
      _isCameraStarting = false;
    });
    final detail = message.isEmpty ? 'Live camera error.' : message;
    final normalized = detail.toLowerCase();
    widget.onTechnicalError?.call(
      normalized.contains('mediapipe')
          ? 'mediapipe_error'
          : normalized.contains('permission')
          ? 'camera_permission_issue'
          : 'camera_error',
      detail,
    );
  }

  void _handleLiveFrame(LiveLandmarkFrame frame) {
    if (!mounted) {
      return;
    }
    setState(() {
      _lastFrame = frame;
    });
  }

  void _handleCaptureProgress(int validFrameCount, int requiredFrameCount) {
    if (!mounted) {
      return;
    }
    setState(() {
      _validFrameCount = validFrameCount;
      _isCapturing = validFrameCount < requiredFrameCount;
    });
  }

  Future<void> _handleCaptureComplete(
    List<List<double>> frames,
    LiveCaptureMetrics metrics,
  ) async {
    final recognitionService = _recognitionService;
    if (recognitionService == null) {
      return;
    }

    setState(() {
      _isCapturing = false;
      _isPredicting = true;
      _statusMessage = 'Sign captured. Checking the banking intent...';
    });

    try {
      final session = recognitionService.predictFromFrames(
        frames: frames,
        mode: SignMode.bankingIntent,
        captureMetrics: metrics,
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _session = session;
        _isPredicting = false;
        _validFrameCount = metrics.validFrameCount;
        _statusMessage = session.prediction.decision.accepted
            ? 'Banking intent recognized.'
            : 'The sign could not be recognized confidently.';
      });
      widget.onPrediction?.call(session.prediction);
      widget.onSession?.call(session);
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _isPredicting = false;
        _errorMessage = _showDeveloperDetails
            ? error.toString()
            : 'The sign could not be processed. Please try again.';
        _statusMessage = 'Live prediction failed.';
      });
      final detail = error.toString();
      widget.onTechnicalError?.call(
        detail.toLowerCase().contains('finite')
            ? 'non_finite_output'
            : 'prediction_processing_failure',
        detail,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = _session;
    final lastFrame = _lastFrame;

    final content = SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _Header(statusMessage: _statusMessage, bankingOnly: true),
          if (_errorMessage != null) ...[
            const SizedBox(height: 12),
            _ErrorPanel(message: _errorMessage!),
          ],
          const SizedBox(height: 12),
          _CameraPreviewCard(preview: _landmarkService.buildPreview()),
          const SizedBox(height: 12),
          _LiveStatusCard(
            bankingOnly: true,
            modelLoaded: _classifier?.isLoaded ?? false,
            cameraStarted: _isCameraStarted,
            lastFrame: lastFrame,
            validFrameCount: _validFrameCount,
            isCapturing: _isCapturing,
          ),
          const SizedBox(height: 12),
          _ControlPanel(
            bankingOnly: true,
            isLoading: _isLoading,
            isCameraStarting: _isCameraStarting,
            isCameraStarted: _isCameraStarted,
            isCapturing: _isCapturing,
            isPredicting: _isPredicting,
            captureLocked:
                widget.captureLocked ||
                (widget.lockAfterSession && session != null),
            onStartCamera: _startCamera,
            onStopCamera: _stopCamera,
            onStartCapture: _startCapture,
            onResetCapture: _resetCapture,
            onCancel: widget.onCancel,
          ),
          if (session != null) ...[
            const SizedBox(height: 12),
            _BankingPredictionNotice(
              prediction: session.prediction,
              onTryAgain: _resetCapture,
              allowTryAgain: widget.allowTryAgain,
            ),
          ],
          if (session != null && _showDeveloperDetails) ...[
            const SizedBox(height: 12),
            _RuntimeMetricsCard(session: session),
            const SizedBox(height: 12),
            TopPredictionsList(
              title: 'Final 40-Class Top Predictions',
              predictions: session.prediction.topPredictions,
            ),
          ],
          const SizedBox(height: 12),
          const _PrivacyCard(),
        ],
      ),
    );

    if (widget.embedded) {
      return content;
    }
    return Scaffold(
      appBar: AppBar(title: const Text('Final Model Live Diagnostics')),
      body: content,
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.statusMessage, required this.bankingOnly});

  final String statusMessage;
  final bool bankingOnly;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          bankingOnly
              ? 'Final 40-Class Banking Recognition'
              : 'Final 40-Class Banking Recognition',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
        ),
        if (bankingOnly) ...[
          const SizedBox(height: 6),
          const Text(
            'Position your hands clearly and perform one banking sign.',
          ),
          const SizedBox(height: 8),
          const Chip(
            key: ValueKey('banking-mode-active'),
            avatar: Icon(Icons.account_balance_outlined),
            label: Text('Banking signs only'),
          ),
        ],
        const SizedBox(height: 4),
        Text(
          statusMessage,
          style: TextStyle(
            color: Theme.of(context).colorScheme.primary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _CameraPreviewCard extends StatelessWidget {
  const _CameraPreviewCard({required this.preview});

  final Widget preview;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: AspectRatio(aspectRatio: 3 / 4, child: preview),
    );
  }
}

class _LiveStatusCard extends StatelessWidget {
  const _LiveStatusCard({
    required this.bankingOnly,
    required this.modelLoaded,
    required this.cameraStarted,
    required this.lastFrame,
    required this.validFrameCount,
    required this.isCapturing,
  });

  final bool bankingOnly;
  final bool modelLoaded;
  final bool cameraStarted;
  final LiveLandmarkFrame? lastFrame;
  final int validFrameCount;
  final bool isCapturing;

  @override
  Widget build(BuildContext context) {
    final frame = lastFrame;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              bankingOnly ? 'Recognition Progress' : 'Live Pipeline Status',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            if (!bankingOnly)
              _StatusRow(
                label: 'TFLite model',
                value: modelLoaded ? 'Loaded' : 'Loading',
              ),
            _StatusRow(
              label: 'Camera preview',
              value: cameraStarted ? 'Started' : 'Stopped',
            ),
            _StatusRow(
              label: 'Hand detected',
              value: frame?.handDetected == true ? 'Yes' : 'No',
            ),
            if (!bankingOnly)
              _StatusRow(
                label: 'Frame dimension',
                value: frame?.isValid == true
                    ? AppConfig.expectedFrameWidth.toString()
                    : 'Waiting',
              ),
            _StatusRow(
              label: bankingOnly ? 'Capture progress' : 'Valid frame buffer',
              value: '$validFrameCount / ${AppConfig.expectedFrameCount}',
            ),
            if (isCapturing) const SizedBox(height: 8),
            if (isCapturing)
              LinearProgressIndicator(
                value: validFrameCount / AppConfig.expectedFrameCount,
              ),
          ],
        ),
      ),
    );
  }
}

class _ControlPanel extends StatelessWidget {
  const _ControlPanel({
    required this.bankingOnly,
    required this.isLoading,
    required this.isCameraStarting,
    required this.isCameraStarted,
    required this.isCapturing,
    required this.isPredicting,
    required this.captureLocked,
    required this.onStartCamera,
    required this.onStopCamera,
    required this.onStartCapture,
    required this.onResetCapture,
    required this.onCancel,
  });

  final bool bankingOnly;
  final bool isLoading;
  final bool isCameraStarting;
  final bool isCameraStarted;
  final bool isCapturing;
  final bool isPredicting;
  final bool captureLocked;
  final VoidCallback onStartCamera;
  final VoidCallback onStopCamera;
  final VoidCallback onStartCapture;
  final VoidCallback onResetCapture;
  final VoidCallback? onCancel;

  @override
  Widget build(BuildContext context) {
    final baseDisabled = isLoading || isCameraStarting || isPredicting;
    final captureDisabled = baseDisabled || captureLocked;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            FilledButton.icon(
              onPressed: captureDisabled || isCameraStarted
                  ? null
                  : onStartCamera,
              icon: isCameraStarting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.videocam),
              label: const Text('Start Camera'),
            ),
            OutlinedButton.icon(
              onPressed: baseDisabled || !isCameraStarted ? null : onStopCamera,
              icon: const Icon(Icons.videocam_off),
              label: const Text('Stop'),
            ),
            FilledButton.icon(
              onPressed: captureDisabled || !isCameraStarted || isCapturing
                  ? null
                  : onStartCapture,
              icon: const Icon(Icons.back_hand),
              label: Text(bankingOnly ? 'Capture Sign' : 'Capture 60 Frames'),
            ),
            OutlinedButton.icon(
              onPressed: captureDisabled ? null : onResetCapture,
              icon: const Icon(Icons.restart_alt),
              label: const Text('Reset'),
            ),
            if (bankingOnly && onCancel != null)
              TextButton.icon(
                onPressed: captureDisabled ? null : onCancel,
                icon: const Icon(Icons.close),
                label: const Text('Cancel'),
              ),
          ],
        ),
      ),
    );
  }
}

class _BankingPredictionNotice extends StatelessWidget {
  const _BankingPredictionNotice({
    required this.prediction,
    required this.onTryAgain,
    required this.allowTryAgain,
  });

  final PredictionResult prediction;
  final VoidCallback onTryAgain;
  final bool allowTryAgain;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final evaluation = const BankingPredictionGate().evaluate(prediction);
    final accepted = evaluation.accepted;
    return Card(
      color: accepted ? colors.primaryContainer : colors.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              accepted ? Icons.check_circle_outline : Icons.refresh,
              color: accepted
                  ? colors.onPrimaryContainer
                  : colors.onErrorContainer,
            ),
            const SizedBox(height: 8),
            Text(
              accepted ? 'Banking intent recognized.' : evaluation.message,
              style: TextStyle(
                color: accepted
                    ? colors.onPrimaryContainer
                    : colors.onErrorContainer,
                fontWeight: FontWeight.w700,
              ),
            ),
            if (!accepted && allowTryAgain) ...[
              const SizedBox(height: 12),
              FilledButton.icon(
                key: const ValueKey('recognition-try-again'),
                onPressed: onTryAgain,
                icon: const Icon(Icons.refresh),
                label: const Text('Try Again'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _RuntimeMetricsCard extends StatelessWidget {
  const _RuntimeMetricsCard({required this.session});

  final LivePredictionSession session;

  @override
  Widget build(BuildContext context) {
    final metrics = session.captureMetrics;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Runtime Metrics',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            _StatusRow(
              label: 'Feature vector length',
              value: session.featureLength.toString(),
            ),
            _StatusRow(
              label: 'Captured frames',
              value: metrics.validFrameCount.toString(),
            ),
            _StatusRow(
              label: 'Frame dimension',
              value: metrics.frameDimension.toString(),
            ),
            _StatusRow(
              label: 'Capture duration',
              value: '${metrics.captureDurationMs} ms',
            ),
            _StatusRow(
              label: 'Average capture FPS',
              value: metrics.averageFps.toStringAsFixed(2),
            ),
            _StatusRow(
              label: 'Feature computation',
              value: '${session.featureComputationMs} ms',
            ),
            _StatusRow(
              label: 'TFLite inference',
              value: '${session.inferenceMs} ms',
            ),
            _StatusRow(
              label: 'End-to-end prediction',
              value: '${session.endToEndMs} ms',
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorPanel extends StatelessWidget {
  const _ErrorPanel({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFFFFF1F2),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.error_outline, color: Color(0xFFBE123C)),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(color: Color(0xFF9F1239)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PrivacyCard extends StatelessWidget {
  const _PrivacyCard();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.lock_outline, color: Color(0xFF0F766E)),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Camera frames, landmarks, feature computation, and TFLite inference stay on the Android device. No video upload or server processing is used.',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
