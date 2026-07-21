import 'dart:async';

import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../controllers/technical_evaluation_controller.dart';
import '../models/live_prediction_session.dart';
import '../models/technical_evaluation.dart';
import '../services/evaluation_schedule_service.dart';
import '../services/technical_evaluation_store.dart';
import '../theme/signsync_theme.dart';
import 'live_camera_page.dart';
import 'widgets/privacy_status_chip.dart';

class FinalTechnicalEvaluationPage extends StatefulWidget {
  const FinalTechnicalEvaluationPage({
    super.key,
    this.scheduleLoader,
    this.platformService = const TechnicalEvaluationPlatformService(),
  });

  final Future<List<EvaluationTrial>> Function()? scheduleLoader;
  final TechnicalEvaluationPlatformService platformService;

  @override
  State<FinalTechnicalEvaluationPage> createState() =>
      _FinalTechnicalEvaluationPageState();
}

class _FinalTechnicalEvaluationPageState
    extends State<FinalTechnicalEvaluationPage> {
  TechnicalEvaluationController? _controller;
  String _status = 'Loading the frozen Sprint 2.19 protocol...';
  String? _error;
  bool _loading = true;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _loadSchedule();
  }

  @override
  void dispose() {
    _controller?.removeListener(_handleControllerChanged);
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _loadSchedule() async {
    try {
      final rows =
          await (widget.scheduleLoader?.call() ??
              const EvaluationScheduleService().loadFrozenSchedule());
      final controller = TechnicalEvaluationController(schedule: rows)
        ..addListener(_handleControllerChanged);
      if (!mounted) {
        controller.dispose();
        return;
      }
      setState(() {
        _controller = controller;
        _loading = false;
        _status = 'Protocol ready. Create or resume a named session.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _loading = false;
        _error = error.toString();
        _status = 'The frozen evaluation protocol could not be loaded.';
      });
    }
  }

  void _handleControllerChanged() {
    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _startOrResumeSession() async {
    final sessionId = await _requestSessionId();
    if (sessionId == null || !mounted) {
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _status = 'Preparing local evaluation storage and device metadata...';
    });
    try {
      final directory = await widget.platformService.getEvaluationDirectory();
      final device = await widget.platformService.getDeviceInfo();
      if (device.packageId != AppConfig.androidPackageId) {
        throw StateError('Android package ID does not match the frozen app.');
      }
      await _controller!.startOrResume(
        sessionId: sessionId,
        persistence: FileTechnicalEvaluationPersistence(
          directoryPath: directory,
        ),
        device: device,
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _busy = false;
        _status = _controller!.warmUpComplete
            ? 'Session resumed. Continue the frozen schedule.'
            : 'Complete five excluded warm-up captures before Trial 1.';
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _busy = false;
        _error = error.toString();
        _status = 'Evaluation session could not start.';
      });
    }
  }

  Future<String?> _requestSessionId() async {
    final textController = TextEditingController(
      text: 'a55_${DateTime.now().toUtc().toIso8601String().substring(0, 10)}',
    );
    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Create or resume evaluation'),
        content: TextField(
          key: const ValueKey('evaluation-session-id'),
          controller: textController,
          maxLength: 64,
          decoration: const InputDecoration(
            labelText: 'Session ID',
            helperText: 'Use the same ID to resume saved progress.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () =>
                Navigator.of(dialogContext).pop(textController.text),
            child: const Text('Continue'),
          ),
        ],
      ),
    );
    textController.dispose();
    return result;
  }

  Future<void> _handleLiveSession(LivePredictionSession session) async {
    final controller = _controller!;
    try {
      final outcome = await controller.recordLiveSession(session);
      if (!mounted) {
        return;
      }
      setState(() {
        _status = outcome == EvaluationRecordOutcome.warmUpRecorded
            ? 'Warm-up ${controller.warmUpsCompleted} / 5 recorded and excluded.'
            : 'Formal first result saved. Confirm to continue; it cannot be edited.';
      });
    } catch (error) {
      if (mounted) {
        setState(() => _error = error.toString());
      }
    }
  }

  Future<void> _recordAutomaticError(String eventType, String message) async {
    final controller = _controller;
    if (controller == null || !controller.hasSession) {
      return;
    }
    await controller.recordTechnicalFailure(
      eventType: eventType,
      message: message,
    );
  }

  Future<void> _recordCaptureReset() async {
    final controller = _controller;
    if (controller == null || !controller.hasSession) {
      return;
    }
    await controller.recordTechnicalFailure(
      eventType: 'capture_cancelled',
      message: 'Capture reset before a valid inference completed.',
    );
  }

  Future<void> _chooseTechnicalFailure() async {
    const choices = <String, String>{
      'no_hands_detected': 'No hands detected',
      'insufficient_valid_frames': 'Fewer than 60 valid frames',
      'camera_unavailable': 'Camera unavailable',
      'camera_permission_issue': 'Camera permission issue',
      'mediapipe_error': 'MediaPipe error',
      'app_backgrounded': 'App backgrounded during capture',
      'model_load_failure': 'Model-load failure',
      'non_finite_output': 'Non-finite model output',
      'app_crash': 'App crash',
      'forced_restart': 'Forced app restart',
      'evaluation_resumed': 'Evaluation resumed after restart',
      'export_failure': 'Evaluation export failure',
      'data_integrity_failure': 'Evaluation data-integrity failure',
      'other_technical_failure': 'Other technical failure',
    };
    final selected = await showDialog<String>(
      context: context,
      builder: (dialogContext) => SimpleDialog(
        title: const Text('Log technical event'),
        children: choices.entries
            .map(
              (entry) => SimpleDialogOption(
                onPressed: () => Navigator.of(dialogContext).pop(entry.key),
                child: Text(entry.value),
              ),
            )
            .toList(growable: false),
      ),
    );
    if (selected == null) {
      return;
    }
    await _controller!.recordTechnicalFailure(
      eventType: selected,
      message: choices[selected]!,
    );
    if (mounted) {
      setState(() {
        _status = 'Technical event logged. Repeat the same scheduled trial.';
      });
    }
  }

  Future<void> _confirmAndAdvance() async {
    await _controller!.confirmAndAdvance();
    if (mounted) {
      setState(() {
        _status = _controller!.isComplete
            ? 'All 400 formal results are complete. Export the session.'
            : 'Result locked. Continue with the displayed scheduled sign.';
      });
    }
  }

  Future<void> _togglePause() async {
    if (_controller!.paused) {
      await _controller!.resume();
    } else {
      await _controller!.pause();
    }
  }

  Future<void> _export() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final export = await _controller!.exportCompletedSession();
      if (mounted) {
        setState(() {
          _busy = false;
          _status = 'Export complete: ${export.directoryPath}';
        });
      }
    } catch (error) {
      await _controller!.recordTechnicalFailure(
        eventType: 'export_failure',
        message: error.toString(),
      );
      if (mounted) {
        setState(() {
          _busy = false;
          _error = error.toString();
        });
      }
    }
  }

  Future<void> _clearSession() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Clear evaluation session?'),
        content: const Text(
          'This removes only local Sprint 2.19 evaluation progress and exports. '
          'It does not touch phone dataset samples or banking interactions.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Clear Session'),
          ),
        ],
      ),
    );
    if (confirmed != true) {
      return;
    }
    await _controller!.clearSession(confirmed: true);
    if (mounted) {
      setState(() {
        _status = 'Evaluation session cleared after explicit confirmation.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    return Scaffold(
      appBar: AppBar(title: const Text('Final Technical Evaluation')),
      body: SafeArea(
        child: _loading || controller == null
            ? const Center(child: CircularProgressIndicator())
            : controller.hasSession
            ? _buildActiveSession(controller)
            : _buildProtocolStart(controller),
      ),
    );
  }

  Widget _buildProtocolStart(TechnicalEvaluationController controller) {
    return ListView(
      padding: const EdgeInsets.all(SignSyncTheme.spaceMd),
      children: [
        Text(
          'Controlled live-device recognition study',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        const PrivacyStatusChip(
          icon: Icons.lock_outline,
          label: 'Developer research tool - local only',
        ),
        const SizedBox(height: 16),
        const _ProtocolCard(),
        const SizedBox(height: 12),
        _StatusPanel(status: _status, error: _error),
        const SizedBox(height: 12),
        FilledButton.icon(
          key: const ValueKey('start-evaluation-session'),
          onPressed: _busy ? null : _startOrResumeSession,
          icon: const Icon(Icons.science_outlined),
          label: const Text('Create or Resume Session'),
        ),
      ],
    );
  }

  Widget _buildActiveSession(TechnicalEvaluationController controller) {
    final trial = controller.currentTrial;
    final latest = controller.latestResult;
    return Column(
      children: [
        EvaluationProgressHeader(
          controller: controller,
          trial: trial,
          latest: latest,
          status: _status,
          error: _error,
        ),
        Expanded(
          child: LiveCameraPage(
            key: ValueKey('evaluation-camera-${controller.sessionId}'),
            embedded: true,
            bankingOnly: true,
            captureLocked: controller.captureLocked,
            allowTryAgain: false,
            lockAfterSession: true,
            captureCycleToken: controller.warmUpComplete
                ? 'trial-${trial?.trialNumber ?? 'complete'}'
                : 'warmup-${controller.warmUpsCompleted + 1}',
            onSession: _handleLiveSession,
            onTechnicalError: _recordAutomaticError,
            onCaptureReset: _recordCaptureReset,
          ),
        ),
        _EvaluationActionBar(
          controller: controller,
          busy: _busy,
          onConfirm: _confirmAndAdvance,
          onPause: _togglePause,
          onLogFailure: _chooseTechnicalFailure,
          onExport: _export,
          onClear: _clearSession,
        ),
      ],
    );
  }
}

class _ProtocolCard extends StatelessWidget {
  const _ProtocolCard();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            _ProtocolRow(
              label: 'Protocol',
              value: AppConfig.evaluationProtocolVersion,
            ),
            _ProtocolRow(label: 'Schedule', value: '10 blocks / 400 trials'),
            _ProtocolRow(label: 'Conditions', value: '200 standard / 200 mild'),
            _ProtocolRow(label: 'Warm-up', value: '5 excluded captures'),
            _ProtocolRow(label: 'Threshold', value: '0.80 frozen'),
            _ProtocolRow(label: 'Model', value: AppConfig.modelVersion),
            _ProtocolRow(
              label: 'Model SHA-256',
              value: AppConfig.activeDynamicModelSha256,
            ),
            SizedBox(height: 8),
            Text(
              'Only technical metadata is stored. Camera images, video, raw '
              'frames, landmarks, features, and customer banking data are never exported.',
            ),
          ],
        ),
      ),
    );
  }
}

class EvaluationProgressHeader extends StatelessWidget {
  const EvaluationProgressHeader({
    super.key,
    required this.controller,
    required this.trial,
    required this.latest,
    required this.status,
    required this.error,
  });

  final TechnicalEvaluationController controller;
  final EvaluationTrial? trial;
  final EvaluationTrialResult? latest;
  final String status;
  final String? error;

  @override
  Widget build(BuildContext context) {
    final warmUp = !controller.warmUpComplete;
    return Material(
      color: Theme.of(context).colorScheme.surfaceContainer,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    warmUp
                        ? 'Excluded warm-up ${controller.warmUpsCompleted + 1} / 5'
                        : controller.isComplete
                        ? 'Formal evaluation complete'
                        : 'Trial ${trial!.trialNumber} / 400 - Block ${trial!.blockNumber}',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                Text('${controller.completedTrialCount}/400'),
              ],
            ),
            if (!warmUp && trial != null) ...[
              const SizedBox(height: 4),
              Text(
                '${trial!.condition.displayName}: ${trial!.intendedLabel}',
                key: const ValueKey('evaluation-current-trial'),
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ],
            if (latest != null && controller.awaitingAdvance)
              Text(
                'Saved: ${latest!.predictedLabel} '
                '(${(latest!.confidence * 100).toStringAsFixed(2)}%) - '
                '${latest!.accepted ? 'accepted' : 'rejected'}',
                key: const ValueKey('evaluation-immutable-result'),
              ),
            Text(status, maxLines: 2, overflow: TextOverflow.ellipsis),
            if (error != null)
              Text(
                error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
          ],
        ),
      ),
    );
  }
}

class _EvaluationActionBar extends StatelessWidget {
  const _EvaluationActionBar({
    required this.controller,
    required this.busy,
    required this.onConfirm,
    required this.onPause,
    required this.onLogFailure,
    required this.onExport,
    required this.onClear,
  });

  final TechnicalEvaluationController controller;
  final bool busy;
  final VoidCallback onConfirm;
  final VoidCallback onPause;
  final VoidCallback onLogFailure;
  final VoidCallback onExport;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 4,
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              if (controller.awaitingAdvance)
                FilledButton.icon(
                  key: const ValueKey('evaluation-confirm-result'),
                  onPressed: busy ? null : onConfirm,
                  icon: const Icon(Icons.lock_outline),
                  label: const Text('Confirm & Continue'),
                ),
              IconButton(
                tooltip: controller.paused
                    ? 'Resume evaluation'
                    : 'Pause evaluation',
                onPressed: busy || controller.isComplete ? null : onPause,
                icon: Icon(controller.paused ? Icons.play_arrow : Icons.pause),
              ),
              IconButton(
                tooltip: 'Log technical failure',
                onPressed: busy || controller.awaitingAdvance
                    ? null
                    : onLogFailure,
                icon: const Icon(Icons.report_problem_outlined),
              ),
              IconButton(
                tooltip: 'Export completed session',
                onPressed: busy || !controller.isComplete ? null : onExport,
                icon: const Icon(Icons.file_download_outlined),
              ),
              IconButton(
                tooltip: 'Clear evaluation session',
                onPressed: busy ? null : onClear,
                icon: const Icon(Icons.delete_outline),
              ),
              Chip(label: Text('${controller.technicalEventCount} events')),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProtocolRow extends StatelessWidget {
  const _ProtocolRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: Text(label)),
          const SizedBox(width: 12),
          Expanded(
            flex: 2,
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

class _StatusPanel extends StatelessWidget {
  const _StatusPanel({required this.status, required this.error});

  final String status;
  final String? error;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(status),
            if (error != null) ...[
              const SizedBox(height: 6),
              Text(
                error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
