import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:smartcart_app/features/auth/data/session_refresher.dart';

void main() {
  test('concurrent refreshes share one rotation', () async {
    var rotations = 0;
    final completer = Completer<String?>();
    final refresher = SessionRefresher(() {
      rotations += 1;
      return completer.future;
    });

    final results = [
      refresher.refresh(),
      refresher.refresh(),
      refresher.refresh(),
    ];
    completer.complete('access-2');

    expect(await Future.wait(results), everyElement('access-2'));
    expect(rotations, 1);
  });

  test('a refresh after the previous one finished rotates again', () async {
    var rotations = 0;
    final refresher = SessionRefresher(() async {
      rotations += 1;
      return 'access-$rotations';
    });

    expect(await refresher.refresh(), 'access-1');
    expect(await refresher.refresh(), 'access-2');
    expect(rotations, 2);
  });

  test('a failed rotation is not cached for the next caller', () async {
    var attempts = 0;
    final refresher = SessionRefresher(() async {
      attempts += 1;
      if (attempts == 1) {
        throw StateError('network down');
      }
      return 'access-ok';
    });

    await expectLater(refresher.refresh(), throwsStateError);
    expect(await refresher.refresh(), 'access-ok');
  });
}
