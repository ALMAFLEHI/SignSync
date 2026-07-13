import 'package:flutter/material.dart';
import 'package:flutter_app/config/phone_dataset_scope.dart';
import 'package:flutter_app/ui/phone_dataset_collection_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'shows exactly the 36 remaining labels and protected pilot summary',
    (tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: PhoneDatasetCollectionPage()),
      );
      await tester.pumpAndSettle();

      expect(
        find.text('Sprint 2.16B Full Banking Intent Expansion'),
        findsOneWidget,
      );
      expect(find.text('Sprint 2.16A Completed (Protected)'), findsOneWidget);
      expect(find.text('0 / 900'), findsOneWidget);
      expect(find.text('0 / 36'), findsOneWidget);
      for (final label in PhoneDatasetScope.sprint216APilotIntents) {
        expect(find.text(label), findsOneWidget);
      }
      await _showLabelSelector(tester);
      for (final label in PhoneDatasetScope.sprint216BRemainingBankingIntents) {
        expect(find.text(label), findsOneWidget);
      }
    },
  );

  testWidgets('requires confirmation before changing the selected label', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(home: PhoneDatasetCollectionPage()),
    );
    await tester.pumpAndSettle();
    await _showLabelSelector(tester);
    final withdrawLabel = find.text('withdraw');
    await tester.ensureVisible(withdrawLabel);
    await tester.tap(withdrawLabel);
    await tester.pumpAndSettle();

    expect(find.text('Change collection label?'), findsOneWidget);
    expect(
      find.textContaining('Move from deposit to withdraw?'),
      findsOneWidget,
    );
    await tester.tap(find.text('Change Label'));
    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('Selected withdraw.'),
      -400,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();

    expect(find.text('Selected withdraw.'), findsOneWidget);
  });
}

Future<void> _showLabelSelector(WidgetTester tester) async {
  await tester.scrollUntilVisible(
    find.text('Remaining Banking Intent'),
    400,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pumpAndSettle();
}
