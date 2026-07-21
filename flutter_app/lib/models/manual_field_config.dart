enum ManualFieldType {
  text('text'),
  multilineText('multiline_text'),
  number('number'),
  maskedNumber('masked_number'),
  amount('amount'),
  date('date'),
  time('time'),
  select('select');

  const ManualFieldType(this.id);

  final String id;

  static ManualFieldType parse(Object? value) {
    if (value is! String) {
      throw const FormatException('Manual field type must be a string.');
    }
    return values.firstWhere(
      (type) => type.id == value,
      orElse: () =>
          throw FormatException('Unsupported manual field type: $value.'),
    );
  }
}

class ManualFieldConfig {
  const ManualFieldConfig({
    required this.id,
    required this.label,
    required this.type,
    required this.required,
    required this.placeholder,
    required this.helperText,
    required this.maximumLength,
    required this.options,
    required this.sensitive,
    required this.displayMasked,
  });

  final String id;
  final String label;
  final ManualFieldType type;
  final bool required;
  final String? placeholder;
  final String? helperText;
  final int? maximumLength;
  final List<String> options;
  final bool sensitive;
  final bool displayMasked;

  factory ManualFieldConfig.fromJson(Map<String, Object?> json) {
    return ManualFieldConfig(
      id: _requiredString(json, 'id'),
      label: _requiredString(json, 'label'),
      type: ManualFieldType.parse(json['type']),
      required: _optionalBool(json, 'required'),
      placeholder: _optionalString(json, 'placeholder'),
      helperText: _optionalString(json, 'helper_text'),
      maximumLength: _optionalInt(json, 'maximum_length'),
      options: _stringList(json['options'], key: 'options'),
      sensitive: _optionalBool(json, 'sensitive'),
      displayMasked: _optionalBool(json, 'display_masked'),
    );
  }

  static String _requiredString(Map<String, Object?> json, String key) {
    final value = json[key];
    if (value is! String || value.trim().isEmpty) {
      throw FormatException('$key must be a non-empty string.');
    }
    return value.trim();
  }

  static String? _optionalString(Map<String, Object?> json, String key) {
    final value = json[key];
    if (value == null) {
      return null;
    }
    if (value is! String) {
      throw FormatException('$key must be a string when provided.');
    }
    return value.trim();
  }

  static int? _optionalInt(Map<String, Object?> json, String key) {
    final value = json[key];
    if (value == null) {
      return null;
    }
    if (value is! int) {
      throw FormatException('$key must be an integer when provided.');
    }
    return value;
  }

  static bool _optionalBool(Map<String, Object?> json, String key) {
    final value = json[key];
    if (value == null) {
      return false;
    }
    if (value is! bool) {
      throw FormatException('$key must be a boolean when provided.');
    }
    return value;
  }

  static List<String> _stringList(Object? value, {required String key}) {
    if (value == null) {
      return const [];
    }
    if (value is! List<Object?>) {
      throw FormatException('$key must be a list.');
    }
    return List<String>.unmodifiable(
      value.map((item) {
        if (item is! String || item.trim().isEmpty) {
          throw FormatException('$key must contain non-empty strings.');
        }
        return item.trim();
      }),
    );
  }
}
