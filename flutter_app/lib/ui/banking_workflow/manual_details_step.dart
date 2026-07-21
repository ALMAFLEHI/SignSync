import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../controllers/banking_interaction_controller.dart';
import '../../models/banking_interaction_session.dart';
import '../../models/manual_field_config.dart';
import '../../theme/signsync_theme.dart';

class ManualDetailsStep extends StatefulWidget {
  const ManualDetailsStep({
    super.key,
    required this.controller,
    required this.session,
    required this.onContinue,
    required this.onBack,
    required this.onCancel,
  });

  final BankingInteractionController controller;
  final BankingInteractionSession session;
  final VoidCallback onContinue;
  final VoidCallback onBack;
  final VoidCallback onCancel;

  @override
  State<ManualDetailsStep> createState() => _ManualDetailsStepState();
}

class _ManualDetailsStepState extends State<ManualDetailsStep> {
  final Map<String, TextEditingController> _textControllers =
      <String, TextEditingController>{};
  final Set<String> _revealedFields = <String>{};

  @override
  void initState() {
    super.initState();
    for (final field in widget.controller.selectedManualFields) {
      if (_usesTextController(field.type)) {
        _textControllers[field.id] = TextEditingController(
          text: widget.session.manualFieldValues[field.id] ?? '',
        );
      }
    }
  }

  @override
  void dispose() {
    for (final controller in _textControllers.values) {
      controller.dispose();
    }
    _textControllers.clear();
    _revealedFields.clear();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final fields = widget.controller.selectedManualFields;
    return ListView(
      key: const ValueKey('manual-details-step'),
      padding: const EdgeInsets.all(SignSyncTheme.spaceMd),
      children: [
        Text(
          'Add optional details',
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 6),
        const Text(
          'Enter only the details needed for this request. Information remains in this session.',
        ),
        const SizedBox(height: 18),
        for (final field in fields) ...[
          _buildField(context, field),
          const SizedBox(height: 14),
        ],
        FilledButton.icon(
          key: const ValueKey('manual-details-continue'),
          onPressed: widget.onContinue,
          icon: const Icon(Icons.arrow_forward),
          label: const Text('Review Request'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: widget.onBack,
          icon: const Icon(Icons.arrow_back),
          label: const Text('Back'),
        ),
        const SizedBox(height: 8),
        TextButton(
          onPressed: widget.onCancel,
          child: const Text('Cancel Interaction'),
        ),
      ],
    );
  }

  Widget _buildField(BuildContext context, ManualFieldConfig field) {
    final error = widget.session.validationErrors[field.id];
    switch (field.type) {
      case ManualFieldType.text:
      case ManualFieldType.multilineText:
      case ManualFieldType.number:
      case ManualFieldType.maskedNumber:
      case ManualFieldType.amount:
        return _buildTextField(field, error);
      case ManualFieldType.date:
        return _PickerField(
          key: ValueKey('manual-field-${field.id}'),
          label: _fieldLabel(field),
          value: widget.session.manualFieldValues[field.id],
          placeholder: field.placeholder ?? 'Choose date',
          errorText: error,
          icon: Icons.calendar_today_outlined,
          onPressed: () => _pickDate(field),
        );
      case ManualFieldType.time:
        return _PickerField(
          key: ValueKey('manual-field-${field.id}'),
          label: _fieldLabel(field),
          value: widget.session.manualFieldValues[field.id],
          placeholder: field.placeholder ?? 'Choose time',
          errorText: error,
          icon: Icons.schedule_outlined,
          onPressed: () => _pickTime(field),
        );
      case ManualFieldType.select:
        final currentValue = widget.session.manualFieldValues[field.id];
        return DropdownButtonFormField<String>(
          key: ValueKey('manual-field-${field.id}'),
          initialValue: field.options.contains(currentValue)
              ? currentValue
              : null,
          decoration: InputDecoration(
            labelText: _fieldLabel(field),
            helperText: field.helperText,
            errorText: error,
          ),
          hint: Text(field.placeholder ?? 'Choose an option'),
          items: field.options
              .map(
                (option) => DropdownMenuItem<String>(
                  value: option,
                  child: Text(option),
                ),
              )
              .toList(growable: false),
          onChanged: (value) {
            if (value != null) {
              widget.controller.updateManualField(field.id, value);
            }
          },
        );
    }
  }

  Widget _buildTextField(ManualFieldConfig field, String? error) {
    final isMasked = field.type == ManualFieldType.maskedNumber;
    final isMultiline = field.type == ManualFieldType.multilineText;
    final revealed = _revealedFields.contains(field.id);
    final inputFormatters = <TextInputFormatter>[];
    if (field.type == ManualFieldType.number || isMasked) {
      inputFormatters.add(FilteringTextInputFormatter.digitsOnly);
    } else if (field.type == ManualFieldType.amount) {
      inputFormatters.add(const _AmountInputFormatter());
    }
    return TextFormField(
      key: ValueKey('manual-field-${field.id}'),
      controller: _textControllers[field.id],
      keyboardType: switch (field.type) {
        ManualFieldType.number ||
        ManualFieldType.maskedNumber => TextInputType.number,
        ManualFieldType.amount => const TextInputType.numberWithOptions(
          decimal: true,
        ),
        ManualFieldType.multilineText => TextInputType.multiline,
        _ => TextInputType.text,
      },
      minLines: isMultiline ? 3 : 1,
      maxLines: isMultiline ? 5 : 1,
      maxLength: field.maximumLength,
      obscureText: isMasked && !revealed,
      enableSuggestions: !field.sensitive,
      autocorrect: !field.sensitive,
      inputFormatters: inputFormatters,
      decoration: InputDecoration(
        labelText: _fieldLabel(field),
        hintText: field.placeholder,
        helperText: field.helperText,
        errorText: error,
        suffixIcon: isMasked
            ? IconButton(
                key: ValueKey('manual-field-reveal-${field.id}'),
                tooltip: revealed ? 'Hide value' : 'Reveal value',
                onPressed: () {
                  setState(() {
                    if (revealed) {
                      _revealedFields.remove(field.id);
                    } else {
                      _revealedFields.add(field.id);
                    }
                  });
                },
                icon: Icon(revealed ? Icons.visibility_off : Icons.visibility),
              )
            : null,
      ),
      onChanged: (value) =>
          widget.controller.updateManualField(field.id, value),
    );
  }

  Future<void> _pickDate(ManualFieldConfig field) async {
    final existing = DateTime.tryParse(
      widget.session.manualFieldValues[field.id] ?? '',
    );
    final now = DateTime.now();
    final selected = await showDatePicker(
      context: context,
      initialDate: existing ?? now,
      firstDate: DateTime(now.year - 10),
      lastDate: DateTime(now.year + 10),
    );
    if (selected == null || !mounted) {
      return;
    }
    widget.controller.updateManualField(
      field.id,
      '${selected.year.toString().padLeft(4, '0')}-'
      '${selected.month.toString().padLeft(2, '0')}-'
      '${selected.day.toString().padLeft(2, '0')}',
    );
  }

  Future<void> _pickTime(ManualFieldConfig field) async {
    final parts = (widget.session.manualFieldValues[field.id] ?? '').split(':');
    final existing = parts.length == 2
        ? TimeOfDay(
            hour: int.tryParse(parts[0]) ?? TimeOfDay.now().hour,
            minute: int.tryParse(parts[1]) ?? TimeOfDay.now().minute,
          )
        : TimeOfDay.now();
    final selected = await showTimePicker(
      context: context,
      initialTime: existing,
    );
    if (selected == null || !mounted) {
      return;
    }
    widget.controller.updateManualField(
      field.id,
      '${selected.hour.toString().padLeft(2, '0')}:'
      '${selected.minute.toString().padLeft(2, '0')}',
    );
  }

  String _fieldLabel(ManualFieldConfig field) {
    return field.required ? '${field.label} *' : field.label;
  }

  static bool _usesTextController(ManualFieldType type) {
    return switch (type) {
      ManualFieldType.text ||
      ManualFieldType.multilineText ||
      ManualFieldType.number ||
      ManualFieldType.maskedNumber ||
      ManualFieldType.amount => true,
      _ => false,
    };
  }
}

class _PickerField extends StatelessWidget {
  const _PickerField({
    super.key,
    required this.label,
    required this.value,
    required this.placeholder,
    required this.errorText,
    required this.icon,
    required this.onPressed,
  });

  final String label;
  final String? value;
  final String placeholder;
  final String? errorText;
  final IconData icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return InputDecorator(
      decoration: InputDecoration(labelText: label, errorText: errorText),
      child: Row(
        children: [
          Expanded(
            child: Text(
              value?.isNotEmpty == true ? value! : placeholder,
              style: TextStyle(
                color: value?.isNotEmpty == true
                    ? Theme.of(context).colorScheme.onSurface
                    : Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          IconButton(tooltip: label, onPressed: onPressed, icon: Icon(icon)),
        ],
      ),
    );
  }
}

class _AmountInputFormatter extends TextInputFormatter {
  const _AmountInputFormatter();

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    return RegExp(r'^\d*\.?\d{0,2}$').hasMatch(newValue.text)
        ? newValue
        : oldValue;
  }
}
