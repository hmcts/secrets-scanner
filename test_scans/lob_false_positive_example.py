"""A deliberate false positive, kept so the fix for issue #44 stays verifiable.

TruffleHog's Lob detector matches `test_` followed by 35 word characters, which is
the shape of a Lob test-mode key. The function name below is exactly that shape, so
scanning this directory reports a *verified* Lob credential even though no
credential exists anywhere in this repository.

Reproduce the finding, as the action invokes TruffleHog:

    trufflehog filesystem test_scans --results=verified --json

And confirm the input added for #44 suppresses only that detector:

    trufflehog filesystem test_scans --results=verified --exclude-detectors=lob --json

The window the detector matches can also span an identifier and the text after it,
so a 39-character name plus one following character matches too - which is why the
answer is a detector exclusion rather than a naming convention.
"""


def test_alpha_beta_gamma_delta_epsilon_zeta():
    assert True
