import 'package:flutter/material.dart';

import '../models/query_configuration.dart';
import '../services/query_configuration_service.dart';
import '../theme/signsync_theme.dart';
import 'widgets/content_states.dart';
import 'widgets/intent_preview_card.dart';
import 'widgets/section_header.dart';

class QueryContentPreviewPage extends StatefulWidget {
  const QueryContentPreviewPage({super.key, this.service});

  final QueryConfigurationService? service;

  @override
  State<QueryContentPreviewPage> createState() =>
      _QueryContentPreviewPageState();
}

class _QueryContentPreviewPageState extends State<QueryContentPreviewPage> {
  late final QueryConfigurationService _service;
  final TextEditingController _searchController = TextEditingController();

  QueryConfiguration? _configuration;
  String? _error;
  String _searchTerm = '';

  @override
  void initState() {
    super.initState();
    _service = widget.service ?? QueryConfigurationService();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _configuration = null;
      _error = null;
    });
    try {
      final configuration = await _service.load();
      if (!mounted) {
        return;
      }
      setState(() {
        _configuration = configuration;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _error = error.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final configuration = _configuration;
    final normalizedSearch = _searchTerm.trim().toLowerCase();
    final filteredIntents = configuration?.intents
        .where((intent) {
          return normalizedSearch.isEmpty ||
              intent.id.toLowerCase().contains(normalizedSearch) ||
              intent.displayName.toLowerCase().contains(normalizedSearch);
        })
        .toList(growable: false);

    return Scaffold(
      appBar: AppBar(title: const Text('Query Content Preview')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(SignSyncTheme.spaceMd),
          children: [
            const SectionHeader(
              title: 'Frozen banking query content',
              description:
                  'Read-only local content for the final 40 banking intents.',
            ),
            const SizedBox(height: 16),
            if (configuration != null)
              _ValidationSummary(
                intentCount: configuration.intents.length,
                queryCount: configuration.intents.fold<int>(
                  0,
                  (total, intent) => total + intent.queries.length,
                ),
              ),
            const SizedBox(height: 16),
            TextField(
              key: const ValueKey('query-preview-search'),
              controller: _searchController,
              textInputAction: TextInputAction.search,
              decoration: const InputDecoration(
                labelText: 'Search intents',
                hintText: 'Intent ID or display name',
                prefixIcon: Icon(Icons.search),
              ),
              onChanged: (value) {
                setState(() {
                  _searchTerm = value;
                });
              },
            ),
            const SizedBox(height: 16),
            if (_error != null)
              ErrorState(message: _error!, onRetry: _load)
            else if (configuration == null)
              const Center(child: CircularProgressIndicator())
            else if (filteredIntents!.isEmpty)
              const EmptyState(message: 'No banking intents match this search.')
            else
              for (
                var index = 0;
                index < filteredIntents.length;
                index += 1
              ) ...[
                IntentPreviewCard(intent: filteredIntents[index]),
                if (index != filteredIntents.length - 1)
                  const SizedBox(height: 8),
              ],
          ],
        ),
      ),
    );
  }
}

class _ValidationSummary extends StatelessWidget {
  const _ValidationSummary({
    required this.intentCount,
    required this.queryCount,
  });

  final int intentCount;
  final int queryCount;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Container(
      key: const ValueKey('query-validation-summary'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(SignSyncTheme.radius),
        border: Border.all(color: colorScheme.primary),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.verified, color: colorScheme.onPrimaryContainer),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Configuration valid',
                  style: TextStyle(
                    color: colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  '$intentCount intents | $queryCount predefined queries',
                  style: TextStyle(color: colorScheme.onPrimaryContainer),
                ),
                Text(
                  'Local read-only content',
                  style: TextStyle(color: colorScheme.onPrimaryContainer),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
