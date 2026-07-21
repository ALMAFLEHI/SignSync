import 'dart:async';

import 'package:flutter/material.dart';

import '../controllers/banking_interaction_controller.dart';
import '../models/banking_interaction_session.dart';
import '../models/prediction_result.dart';
import '../models/query_configuration.dart';
import '../services/banking_prediction_gate.dart';
import '../services/query_configuration_service.dart';
import '../theme/signsync_theme.dart';
import 'banking_workflow/banker_request_view.dart';
import 'banking_workflow/intent_confirmation_step.dart';
import 'banking_workflow/manual_details_step.dart';
import 'banking_workflow/query_selection_step.dart';
import 'banking_workflow/request_review_step.dart';
import 'live_camera_page.dart';

typedef BankingRecognitionBuilder =
    Widget Function(
      BuildContext context,
      ValueChanged<PredictionResult> onPrediction,
      VoidCallback onCancel,
    );

class BankingInteractionPage extends StatefulWidget {
  const BankingInteractionPage({
    super.key,
    this.queryService,
    this.controller,
    this.recognitionBuilder,
    this.predictionGate = const BankingPredictionGate(),
  });

  final QueryConfigurationService? queryService;
  final BankingInteractionController? controller;
  final BankingRecognitionBuilder? recognitionBuilder;
  final BankingPredictionGate predictionGate;

  @override
  State<BankingInteractionPage> createState() => _BankingInteractionPageState();
}

class _BankingInteractionPageState extends State<BankingInteractionPage> {
  late final QueryConfigurationService _queryService;
  late final BankingInteractionController _controller;
  late final bool _ownsController;

  QueryConfiguration? _configuration;
  String? _configurationError;
  String? _recognitionError;

  @override
  void initState() {
    super.initState();
    _queryService = widget.queryService ?? QueryConfigurationService();
    _ownsController = widget.controller == null;
    _controller = widget.controller ?? BankingInteractionController();
    unawaited(_loadConfiguration());
  }

  @override
  void dispose() {
    _controller.reset(notify: false);
    if (_ownsController) {
      _controller.dispose();
    }
    super.dispose();
  }

  Future<void> _loadConfiguration() async {
    setState(() {
      _configuration = null;
      _configurationError = null;
    });
    try {
      final configuration = await _queryService.load();
      if (!mounted) {
        return;
      }
      setState(() {
        _configuration = configuration;
      });
    } on Object {
      if (!mounted) {
        return;
      }
      setState(() {
        _configurationError = 'Local request content could not be loaded.';
      });
    }
  }

  void _handlePrediction(PredictionResult prediction) {
    final evaluation = widget.predictionGate.evaluate(prediction);
    if (!evaluation.accepted || evaluation.intentId == null) {
      setState(() {
        _recognitionError = evaluation.message;
      });
      return;
    }
    final intent = _intentForId(evaluation.intentId!);
    if (intent == null) {
      setState(() {
        _recognitionError = 'Local request content could not be loaded.';
      });
      return;
    }
    setState(() {
      _recognitionError = null;
    });
    _controller.acceptPrediction(
      intent: intent,
      confidence: prediction.confidence,
    );
  }

  BankingIntentConfig? _intentForId(String id) {
    for (final intent in _configuration?.intents ?? <BankingIntentConfig>[]) {
      if (intent.id == id) {
        return intent;
      }
    }
    return null;
  }

  Future<void> _handleBack() async {
    if (_controller.goBack()) {
      setState(() {
        _recognitionError = null;
      });
      return;
    }
    await _cancelAndExit();
  }

  Future<void> _cancelAndExit() async {
    if (_controller.hasManualData) {
      final clear = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Clear this interaction?'),
          content: const Text(
            'The details entered for this interaction will be removed.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Keep Editing'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text('Clear and Exit'),
            ),
          ],
        ),
      );
      if (clear != true || !mounted) {
        return;
      }
    }
    _clearAndExit();
  }

  void _clearAndExit() {
    _controller.reset();
    if (mounted) {
      Navigator.of(context).pop();
    }
  }

  void _startOver() {
    _controller.reset();
    setState(() {
      _recognitionError = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_configurationError != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Banking Interaction')),
        body: _ConfigurationError(
          message: _configurationError!,
          onRetry: _loadConfiguration,
          onReturnHome: _clearAndExit,
        ),
      );
    }
    if (_configuration == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return PopScope<void>(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) {
          unawaited(_handleBack());
        }
      },
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          final session = _controller.session;
          return Scaffold(
            appBar: AppBar(
              leading: IconButton(
                tooltip: 'Back',
                onPressed: _handleBack,
                icon: const Icon(Icons.arrow_back),
              ),
              title: Text(_titleForStep(session.step)),
            ),
            body: _buildStep(session),
          );
        },
      ),
    );
  }

  Widget _buildStep(BankingInteractionSession session) {
    switch (session.step) {
      case BankingWorkflowStep.recognition:
        final recognitionBuilder =
            widget.recognitionBuilder ?? _defaultRecognitionBuilder;
        return Column(
          children: [
            if (_recognitionError != null)
              _RecognitionError(
                message: _recognitionError!,
                onTryAgain: _startOver,
              ),
            Expanded(
              child: recognitionBuilder(
                context,
                _handlePrediction,
                _cancelAndExit,
              ),
            ),
          ],
        );
      case BankingWorkflowStep.confirmation:
        return IntentConfirmationStep(
          session: session,
          onConfirm: _controller.confirmIntent,
          onTryAgain: _startOver,
          onCancel: _cancelAndExit,
        );
      case BankingWorkflowStep.querySelection:
        return QuerySelectionStep(
          session: session,
          onSelected: _controller.selectQuery,
          onContinue: _controller.continueFromQuerySelection,
          onBack: _controller.goBack,
          onCancel: _cancelAndExit,
        );
      case BankingWorkflowStep.manualDetails:
        return ManualDetailsStep(
          key: ValueKey('manual-details-${session.selectedQuery!.id}'),
          controller: _controller,
          session: session,
          onContinue: _controller.submitManualDetails,
          onBack: _controller.goBack,
          onCancel: _cancelAndExit,
        );
      case BankingWorkflowStep.review:
        return RequestReviewStep(
          controller: _controller,
          session: session,
          onShowToBanker: _controller.showToBanker,
          onEditRequest: _controller.editRequest,
          onEditDetails: _controller.editDetails,
          onStartOver: _startOver,
        );
      case BankingWorkflowStep.bankerView:
        return BankerRequestView(
          controller: _controller,
          session: session,
          onBackToReview: _controller.goBack,
          onNewInteraction: _startOver,
          onClearSession: _clearAndExit,
        );
    }
  }

  Widget _defaultRecognitionBuilder(
    BuildContext context,
    ValueChanged<PredictionResult> onPrediction,
    VoidCallback onCancel,
  ) {
    return LiveCameraPage(
      key: const ValueKey('banking-live-recognition'),
      bankingOnly: true,
      embedded: true,
      onPrediction: onPrediction,
      onCancel: onCancel,
    );
  }

  String _titleForStep(BankingWorkflowStep step) {
    return switch (step) {
      BankingWorkflowStep.recognition => 'Banking Interaction',
      BankingWorkflowStep.confirmation => 'Confirm Intent',
      BankingWorkflowStep.querySelection => 'Select Request',
      BankingWorkflowStep.manualDetails => 'Request Details',
      BankingWorkflowStep.review => 'Review Request',
      BankingWorkflowStep.bankerView => 'Banker View',
    };
  }
}

class _RecognitionError extends StatelessWidget {
  const _RecognitionError({required this.message, required this.onTryAgain});

  final String message;
  final VoidCallback onTryAgain;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      key: const ValueKey('banking-recognition-error'),
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colors.errorContainer,
        borderRadius: BorderRadius.circular(SignSyncTheme.radius),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              message,
              style: TextStyle(color: colors.onErrorContainer),
            ),
          ),
          const SizedBox(width: 8),
          TextButton.icon(
            key: const ValueKey('workflow-recognition-try-again'),
            onPressed: onTryAgain,
            icon: const Icon(Icons.refresh),
            label: const Text('Try Again'),
          ),
        ],
      ),
    );
  }
}

class _ConfigurationError extends StatelessWidget {
  const _ConfigurationError({
    required this.message,
    required this.onRetry,
    required this.onReturnHome,
  });

  final String message;
  final VoidCallback onRetry;
  final VoidCallback onReturnHome;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 42),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
            TextButton(
              onPressed: onReturnHome,
              child: const Text('Return Home'),
            ),
          ],
        ),
      ),
    );
  }
}
