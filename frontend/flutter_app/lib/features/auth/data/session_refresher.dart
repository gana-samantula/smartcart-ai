/// Runs token rotation at most once at a time.
///
/// The API revokes a whole session when a rotated-out refresh token is presented again. Two
/// requests that both get 401 must therefore share one refresh, rather than each rotating the
/// token and replaying the other's.
class SessionRefresher {
  SessionRefresher(this._rotate);

  final Future<String?> Function() _rotate;
  Future<String?>? _inFlight;

  Future<String?> refresh() {
    final pending = _inFlight;
    if (pending != null) {
      return pending;
    }
    final next = _rotate().whenComplete(() => _inFlight = null);
    _inFlight = next;
    return next;
  }
}
