# Changelog

## [1.0.2](https://github.com/CHIMEFRB/datatrail-cli/compare/datatrail-cli-v1.0.1...datatrail-cli-v1.0.2) (2026-09-29)


### Documentation

* cover readiness, verification, and recursive discovery ([#201](https://github.com/CHIMEFRB/datatrail-cli/issues/201)) ([b7b4808](https://github.com/CHIMEFRB/datatrail-cli/commit/b7b48084b094f89ce5812182ac85b487478057d7))
* restore standalone GitHub Pages build ([#199](https://github.com/CHIMEFRB/datatrail-cli/issues/199)) ([476935e](https://github.com/CHIMEFRB/datatrail-cli/commit/476935e9530f196f64ea2551deb89f65f0fece55))

## [1.0.1](https://github.com/CHIMEFRB/datatrail-cli/compare/datatrail-cli-v1.0.0...datatrail-cli-v1.0.1) (2026-09-29)


### Bug Fixes

* **pull:** continue when optional size query is unavailable ([#195](https://github.com/CHIMEFRB/datatrail-cli/issues/195)) ([b36bbbf](https://github.com/CHIMEFRB/datatrail-cli/commit/b36bbbf90d47eb22f20eaa7a12cfea8f4ae703bb))
* **scout:** restore discrepancy detection and confirmed repairs ([#197](https://github.com/CHIMEFRB/datatrail-cli/issues/197)) ([54dfbf4](https://github.com/CHIMEFRB/datatrail-cli/commit/54dfbf4b3abf8ff0f7f9db13e5eb7ccdb28ccce1))


### Performance Improvements

* **pull:** apply CANFAR permissions without subprocesses ([#157](https://github.com/CHIMEFRB/datatrail-cli/issues/157)) ([b8c2230](https://github.com/CHIMEFRB/datatrail-cli/commit/b8c22306432a6b24b435b5ddb421ac5cdcd9e1eb))

## [1.0.0](https://github.com/CHIMEFRB/datatrail-cli/compare/datatrail-cli-v0.13.0...datatrail-cli-v1.0.0) (2026-09-28)


### ⚠ BREAKING CHANGES

* require Python 3.10 for patched dependencies

### Features

* **doctor:** add readiness checks ([ae0565c](https://github.com/CHIMEFRB/datatrail-cli/commit/ae0565cd7963758e465889f312f0fac2d0418c3d))
* **doctor:** add readiness checks ([6691c31](https://github.com/CHIMEFRB/datatrail-cli/commit/6691c31cb20e5419588af7a21f62810aee1fbc02))
* **inventory:** add resumable manifests ([c7c4df5](https://github.com/CHIMEFRB/datatrail-cli/commit/c7c4df5d1634e8573f700ba2b1368105f4f67fb7))
* **inventory:** add resumable manifests ([343a28a](https://github.com/CHIMEFRB/datatrail-cli/commit/343a28a74366f91b8a0bd428250f1576cd4a752f))
* **ls:** add --match and --expand for dataset discovery ([bf08635](https://github.com/CHIMEFRB/datatrail-cli/commit/bf08635a75f6ec3b1415541ff1b9a1f31e9d443b))
* **ls:** add match and expand for dataset discovery ([31cccde](https://github.com/CHIMEFRB/datatrail-cli/commit/31cccde47ee8827aec17df7ce13ba5a7ac7b13d3))
* **ls:** add recursive dataset discovery ([8ea3bc4](https://github.com/CHIMEFRB/datatrail-cli/commit/8ea3bc4e5026fbb9fedb231a0bdb7b78a8f90bdf))
* **ls:** add recursive dataset discovery ([6f9a85e](https://github.com/CHIMEFRB/datatrail-cli/commit/6f9a85e608eea73a5b3e8b30331203a09908c71c))
* **ps:** expose common paths in JSON output ([3ee4238](https://github.com/CHIMEFRB/datatrail-cli/commit/3ee423828ee81fca7c9a661051975920e71e17bf))
* **ps:** expose per-storage-element common paths in --json output ([b748fb4](https://github.com/CHIMEFRB/datatrail-cli/commit/b748fb442589a0259b483774ed6fcf391a8eb391))
* **pull:** add resumable manifest transfers ([9017c11](https://github.com/CHIMEFRB/datatrail-cli/commit/9017c118450ee98082f72b4142b2c76d77c94f28))
* **pull:** add resumable manifest transfers ([7272daa](https://github.com/CHIMEFRB/datatrail-cli/commit/7272daa58fc76b3130181fdc1171da7453b01f82))
* **verify:** verify registered dataset files ([cef2ab7](https://github.com/CHIMEFRB/datatrail-cli/commit/cef2ab708b2d4f26bae4131d18f5613ba86ec0e3))
* **verify:** verify registered dataset files ([27f3810](https://github.com/CHIMEFRB/datatrail-cli/commit/27f3810dfe78c1f889cb94abae3836a7058ebfd5))


### Bug Fixes

* add stable command error metadata ([d1096ff](https://github.com/CHIMEFRB/datatrail-cli/commit/d1096ffb850b6bd1a690370318dcec5be97ce4f3))
* **deps:** require patched Requests on Python 3.10 and newer ([e0fb559](https://github.com/CHIMEFRB/datatrail-cli/commit/e0fb55951975d60c202181644c703f280602fa5f))
* **deps:** require patched Requests on Python 3.10+ ([7d1c4ba](https://github.com/CHIMEFRB/datatrail-cli/commit/7d1c4ba3ead33b46cc6c042e554464fca4e78438))
* **deps:** require patched urllib3 on Python 3.10+ ([5a4ad0b](https://github.com/CHIMEFRB/datatrail-cli/commit/5a4ad0bc1a29dcad305cad8ec739dd47e703ef6a))
* **deps:** use patched dependencies on Python 3.10 and newer ([69f0806](https://github.com/CHIMEFRB/datatrail-cli/commit/69f080682a6fa11f18c4acbc890b3c043bc22393))
* **doctor:** handle certificate and authentication failures ([3584b7b](https://github.com/CHIMEFRB/datatrail-cli/commit/3584b7b0d71ee9bc18479bba75e5b10b96ac8ac2))
* **encoding:** use ASCII status output ([a0646d7](https://github.com/CHIMEFRB/datatrail-cli/commit/a0646d7d17e66b7507a7f6019e1cd48c3faf2f9d))
* enforce patched urllib3 on Python 3.10 and newer ([ab12a03](https://github.com/CHIMEFRB/datatrail-cli/commit/ab12a03402cb0ecfec471b2c1941bc3513101762))
* **failure:** add stable command error metadata ([f52a917](https://github.com/CHIMEFRB/datatrail-cli/commit/f52a917acc05a88b4cbe1364ce3d41af8e1af4ae))
* **inventory:** reconcile recovered discovery checkpoints ([2a0bda5](https://github.com/CHIMEFRB/datatrail-cli/commit/2a0bda5751e849503903c96bba65fe530bb016d2))
* **ls:** validate discovery filters and response names ([af2de4f](https://github.com/CHIMEFRB/datatrail-cli/commit/af2de4f3526da507e54dc30f68cc139227f3381b))
* **ps:** preserve paths for duplicate and invalid replicas ([2dae57d](https://github.com/CHIMEFRB/datatrail-cli/commit/2dae57d4654c4a22c81aea17827a5d0f041b977c))
* **pull:** clean up CADC SDK partial downloads ([1b15bff](https://github.com/CHIMEFRB/datatrail-cli/commit/1b15bffaa32b2685669a74f4d18f9d6bb73ee1ef))
* **pull:** protect aliased directory ownership paths ([c03f284](https://github.com/CHIMEFRB/datatrail-cli/commit/c03f284d730fdf1dd9bf2f8dbe5ddda8780324ac))
* **pull:** publish downloads atomically ([b512e5f](https://github.com/CHIMEFRB/datatrail-cli/commit/b512e5f8ba5b6acd3a5a09c68440eb914d9e8d8e))
* **pull:** publish downloads atomically ([bf7846f](https://github.com/CHIMEFRB/datatrail-cli/commit/bf7846f4efb41ea55d3edd3961b19c5da7d79eb3))
* **pull:** report lost workers and clean up failed starts ([bfe5d91](https://github.com/CHIMEFRB/datatrail-cli/commit/bfe5d91d71d130230f5a6b232953e09e34fc8219))
* **pull:** validate manifest paths before creating state ([b0dc320](https://github.com/CHIMEFRB/datatrail-cli/commit/b0dc32064e1859fc90466da5ed2b4a7f62aa8ccd))
* require Python 3.10 for patched dependencies ([07de5af](https://github.com/CHIMEFRB/datatrail-cli/commit/07de5af18da463d514ca4b05da06a749c5c2b0dd))
* update TLS dependencies without raising Python minimum ([8658c58](https://github.com/CHIMEFRB/datatrail-cli/commit/8658c5828ce63772ba229ffa6f4ff93b5c9575fe))
* update TLS dependencies without raising Python minimum ([ec11019](https://github.com/CHIMEFRB/datatrail-cli/commit/ec110197e2f5281cd22261b605de1d1ad47405e3))
* **verify:** preserve reports when metadata services fail ([8dbeea3](https://github.com/CHIMEFRB/datatrail-cli/commit/8dbeea34caa8a87d94f4f4d0e3418f3bcfb2df9f))

## [0.13.0](https://github.com/CHIMEFRB/datatrail-cli/compare/datatrail-cli-v0.12.0...datatrail-cli-v0.13.0) (2026-08-25)


### Features

* **clear:** command to unstage data locally or at arc ([#16](https://github.com/CHIMEFRB/datatrail-cli/issues/16)) ([737c781](https://github.com/CHIMEFRB/datatrail-cli/commit/737c7811a6112a46e842bc135d94d035a9bf301f))
* **clear:** remove empty parent dirs ([#20](https://github.com/CHIMEFRB/datatrail-cli/issues/20)) ([1559608](https://github.com/CHIMEFRB/datatrail-cli/commit/1559608de9d18d1b16a069c5b6b8136afb388fab))
* **cli:** add unregistered command ([d9a97a5](https://github.com/CHIMEFRB/datatrail-cli/commit/d9a97a53b6f87321c50aec34339d6b5959b5e713))
* **cli:** add unregistered command ([b33a6fa](https://github.com/CHIMEFRB/datatrail-cli/commit/b33a6fae57ff2bdad6c26f0ed5402994fdef7650))
* **cli:** aliases ([73ede83](https://github.com/CHIMEFRB/datatrail-cli/commit/73ede838133b54ef0ba8f45eda453547d601a180))
* **cli:** check scope exists ([f14589b](https://github.com/CHIMEFRB/datatrail-cli/commit/f14589bc539ec3448348d1d6bc9b1b32d864d7ea))
* **config:** added datatrail config module ([fe04ee1](https://github.com/CHIMEFRB/datatrail-cli/commit/fe04ee1af77e3d416c103e9ef73a7d79a4b616d5))
* **gh-actions:** ci and cd ([ebb7a96](https://github.com/CHIMEFRB/datatrail-cli/commit/ebb7a966836d2a4f57287191b9396d9b72cb3cfe))
* **ls & ps:** add --json flag for machine readable output ([75dac4d](https://github.com/CHIMEFRB/datatrail-cli/commit/75dac4da4fc172adebe2b518cf0b6136e201d94d))
* **ls & ps:** add --json flag for machine readable output ([c4742a0](https://github.com/CHIMEFRB/datatrail-cli/commit/c4742a0dfe43823ce8e68f21e26e146b90db958c)), closes [#159](https://github.com/CHIMEFRB/datatrail-cli/issues/159)
* **ls,-pull:** partially implemented ([6689d11](https://github.com/CHIMEFRB/datatrail-cli/commit/6689d119782d1e251935050c508fb14969ff33d2))
* **ls,pull:** fully implemented ([2105f5a](https://github.com/CHIMEFRB/datatrail-cli/commit/2105f5a86dc42a0618903d0e315bc6490fd633ed))
* **ls:** option to write ls datasets to disk ([513d665](https://github.com/CHIMEFRB/datatrail-cli/commit/513d665a843bb4aa1f6f92e54ab020ee4f1477ab))
* **ls:** show datasets in given parent dataset ([15f7da1](https://github.com/CHIMEFRB/datatrail-cli/commit/15f7da1aa76a2a0c75f9229e445f96886b353a1f))
* **ls:** show larger datasets ([344e230](https://github.com/CHIMEFRB/datatrail-cli/commit/344e230f9798ad8a27752431bfd70f73370488f8))
* **project:** boilerplate added ([43085a1](https://github.com/CHIMEFRB/datatrail-cli/commit/43085a15789c2045ea41bca9aa89c26c26182019))
* **ps:** function implemented ([6feedde](https://github.com/CHIMEFRB/datatrail-cli/commit/6feedde08b0dddc3c9b43aba17999e681a2c6b1e))
* **ps:** if no files check if dataset is in unregistered bucket and notify user ([40ed903](https://github.com/CHIMEFRB/datatrail-cli/commit/40ed903623a4ec9fd4043b4d1863626303830a54)), closes [#46](https://github.com/CHIMEFRB/datatrail-cli/issues/46)
* **ps:** show num files and size by default, flag to show all files ([cccbd33](https://github.com/CHIMEFRB/datatrail-cli/commit/cccbd3337289699f80112edff612abf746407f4b))
* **pull:** allows specific files to be pulled by designating names o… ([49f186a](https://github.com/CHIMEFRB/datatrail-cli/commit/49f186a6bcdd88e9aad0a863279b06e29b645158))
* **pull:** allows specific files to be pulled by designating names or paths in a local config file ([d3cfb59](https://github.com/CHIMEFRB/datatrail-cli/commit/d3cfb59906fe4cb13c8f549e8c2b6499c32e663e))
* **pull:** check all files were downloaded ([eea76ef](https://github.com/CHIMEFRB/datatrail-cli/commit/eea76efb91b2a35f2900be59d4484d02721322da))
* **pull:** check all files were downloaded ([bb1d8b6](https://github.com/CHIMEFRB/datatrail-cli/commit/bb1d8b64378fe80a27944f8eaccf6ce674ce17d0))
* **pull:** display size of files to be pulled before prompt ([38cffcc](https://github.com/CHIMEFRB/datatrail-cli/commit/38cffccb18dcaca41150ee7af85b4c80f6137284))
* **pull:** implemented multiprocessor pull ([2e7b332](https://github.com/CHIMEFRB/datatrail-cli/commit/2e7b33205789c54e4f9544223a0555d74edd464d))
* **scout:** able to heal missing minoc replicas ([bc3b52d](https://github.com/CHIMEFRB/datatrail-cli/commit/bc3b52d44fe7da7335279c96cec03e3deace6f9a))
* **scout:** add scout command to the cli ([#83](https://github.com/CHIMEFRB/datatrail-cli/issues/83)) ([5cb811f](https://github.com/CHIMEFRB/datatrail-cli/commit/5cb811f416c6fe099cf2405835ad867df125a62d))
* **scout:** generalised scout functionality to check for discrepanci… ([aabcad1](https://github.com/CHIMEFRB/datatrail-cli/commit/aabcad1937fef1734ef17593726d27bb673a29ad))
* **scout:** generalised scout functionality to check for discrepancies between all sites, not just minoc ([f3f1005](https://github.com/CHIMEFRB/datatrail-cli/commit/f3f1005722c48d4ac020b65ed13d19f6bc0bbd48))
* **structure:** added skeleton code ([c3e57f6](https://github.com/CHIMEFRB/datatrail-cli/commit/c3e57f63ea0e54c45f12a4c3682ed01e5d9489ec))
* **unregistered:** command to search for event in unregistered results bucket ([1bb4ca0](https://github.com/CHIMEFRB/datatrail-cli/commit/1bb4ca0c118e042a907f38205af5d7ed6bf9f16d))


### Bug Fixes

* bound every REST call with a request timeout ([431270d](https://github.com/CHIMEFRB/datatrail-cli/commit/431270d2fb4e59acc8a875b578964d20d2aeebb4))
* **cadcclient:** check canfar status ([484562c](https://github.com/CHIMEFRB/datatrail-cli/commit/484562c3c8345dd032c00923d3250c1be4a12191))
* **cadcclient:** improve handling of stdout ([8b35e4f](https://github.com/CHIMEFRB/datatrail-cli/commit/8b35e4f5ccdaf874c706f31a608a89b0612b669d))
* **cadcclient:** improve handling of stdout ([320d4df](https://github.com/CHIMEFRB/datatrail-cli/commit/320d4dfcdd194aa69f9236c84f21dbfb8690068b))
* **cadcclient:** more robust switching of stdout ([9c90315](https://github.com/CHIMEFRB/datatrail-cli/commit/9c9031595a9e13d6471e4b5e5edc548a4d1545ad))
* **ci:** accept request timeout in scopes mock ([1ff9624](https://github.com/CHIMEFRB/datatrail-cli/commit/1ff9624c15045d1acdb30ad471bf6c6a9c298174))
* **ci:** keep fork main credential-free ([9030bfb](https://github.com/CHIMEFRB/datatrail-cli/commit/9030bfb6d971afdb557772d35b1691f531e5e0b4))
* **ci:** keep fork main credential-free ([73a4b02](https://github.com/CHIMEFRB/datatrail-cli/commit/73a4b029178db001025ec5442ce9b9a43911615c))
* **clear:** reorganise file_paths manipulation logic ([fd14f9b](https://github.com/CHIMEFRB/datatrail-cli/commit/fd14f9b714590f1cb57684565cfa23fd7bc8fc52))
* **clear:** reorganise file_paths manipulation logic ([80f0f2d](https://github.com/CHIMEFRB/datatrail-cli/commit/80f0f2d2bf3d9836eef16f9f6d3bed5f88c8ff05))
* **cli-test:** new test - marked as fix to trigger release ([aea98d0](https://github.com/CHIMEFRB/datatrail-cli/commit/aea98d07f63ee17f6d5b4acd396ea32e3aefbd11))
* **cli:** canfar status checks ([7f9df34](https://github.com/CHIMEFRB/datatrail-cli/commit/7f9df349ceeebb1caa7c1c2582cd3d1c54e8ec09))
* **cli:** catch http 503 errors when validating scope ([b6e75af](https://github.com/CHIMEFRB/datatrail-cli/commit/b6e75affe6db6508882ed5e3da1b22bdec194156))
* **cli:** check for luskan status ([b229549](https://github.com/CHIMEFRB/datatrail-cli/commit/b2295493c60f0f2a00a95c1c87eb64a0e926b886))
* **cli:** check for luskan status ([405a3c2](https://github.com/CHIMEFRB/datatrail-cli/commit/405a3c21334b5d8d96ab42436355d8c329880d74))
* **cli:** check minoc status ([a955ab1](https://github.com/CHIMEFRB/datatrail-cli/commit/a955ab129377dbd62215688598cc2cc434345152))
* **cli:** check minoc status ([6a0d6df](https://github.com/CHIMEFRB/datatrail-cli/commit/6a0d6dfc4f3490dc407c08d106d7740bb5d892e3))
* **cli:** print the update-available banner to stderr ([53b9fe4](https://github.com/CHIMEFRB/datatrail-cli/commit/53b9fe4560ff7835a6d7f4e4402538b64f4334aa))
* **cli:** print the update-available banner to stderr ([8dd6313](https://github.com/CHIMEFRB/datatrail-cli/commit/8dd63139b127cf7219932f9d271482a614dc1261))
* **cli:** removed pkg resources deprecation warning ([b488b02](https://github.com/CHIMEFRB/datatrail-cli/commit/b488b024c0f6904bc7f6d66ffff8281791cf59c1))
* **cli:** removed pkg resources deprecation warning ([2ab793d](https://github.com/CHIMEFRB/datatrail-cli/commit/2ab793d753badfd9a2c6aa53ed95010366437c3f))
* **cli:** updated some docs ([4a61228](https://github.com/CHIMEFRB/datatrail-cli/commit/4a61228300d5082e76081d84520fddf743cc0ebf))
* **cli:** wrap version check in try except ([2fc9d31](https://github.com/CHIMEFRB/datatrail-cli/commit/2fc9d3169cc28e675c4cfce51aa142b1f22466c4))
* **config.py:** typo ([#12](https://github.com/CHIMEFRB/datatrail-cli/issues/12)) ([279998b](https://github.com/CHIMEFRB/datatrail-cli/commit/279998bbc5a4c5bd9922db59b159a38fbfdade8b))
* connection errors raise correct status exit code ([9b4d7bc](https://github.com/CHIMEFRB/datatrail-cli/commit/9b4d7bcc74c6a7c6954d965f8ab421ea6181b016))
* **functions.py:** added specific handling for canfar site, where the… ([#66](https://github.com/CHIMEFRB/datatrail-cli/issues/66)) ([895a3ca](https://github.com/CHIMEFRB/datatrail-cli/commit/895a3ca7bdb7000847313ef12fe17e50ad7308c8))
* **functions.py:** changed error catching checks to be for dictionaries with error keys in them as opposed to strings ([#74](https://github.com/CHIMEFRB/datatrail-cli/issues/74)) ([6fdb244](https://github.com/CHIMEFRB/datatrail-cli/commit/6fdb244e46a62253f4654681ec5e5d76431f49f0))
* **functions.py:** patches deletion logic to check that the path to be deleted is greater than 3 levels deep ([#64](https://github.com/CHIMEFRB/datatrail-cli/issues/64)) ([ad43f35](https://github.com/CHIMEFRB/datatrail-cli/commit/ad43f35ce7b8fbc87210ca93df4433b3c4bbe06d))
* **functions:** bug ([f4e3788](https://github.com/CHIMEFRB/datatrail-cli/commit/f4e3788944e5a95f868e139369abdfac35c61caa))
* **functions:** changed return of find_missing_datasets to always ret… ([#76](https://github.com/CHIMEFRB/datatrail-cli/issues/76)) ([a8c0f3d](https://github.com/CHIMEFRB/datatrail-cli/commit/a8c0f3ded414c4e8d4fbca9529bfda7610531841))
* **init:** set valid choices for datatrail config init ([63f96c3](https://github.com/CHIMEFRB/datatrail-cli/commit/63f96c30c07be1d787381e5457021e805ea0cc6f))
* **ls:** other section for scopes that don't match list of sites ([0b50d79](https://github.com/CHIMEFRB/datatrail-cli/commit/0b50d790fbfb21fa0edb16eb945722189333a1c2))
* **ls:** report an unanswered scopes query as an error instead of leaking response text ([6eedaa3](https://github.com/CHIMEFRB/datatrail-cli/commit/6eedaa3720e1f86518fb3ba0292983020affa5af))
* **ls:** report an unanswered scopes query as an error instead of leaking response text ([8fb77d6](https://github.com/CHIMEFRB/datatrail-cli/commit/8fb77d6d1fbb2d724fbec73f84f4768a4d515181))
* **ls:** seperate scopes by site ([5bddcc7](https://github.com/CHIMEFRB/datatrail-cli/commit/5bddcc7b368fa0594128f0f7fcb0b2e26959d77e))
* **ls:** show all larger datasets for scope ([cda63ac](https://github.com/CHIMEFRB/datatrail-cli/commit/cda63ac3053912aa0f4f0bc4781773e3ce46ac0a)), closes [#1](https://github.com/CHIMEFRB/datatrail-cli/issues/1)
* **ps-and-pull:** check if namespace already prepended ([#9](https://github.com/CHIMEFRB/datatrail-cli/issues/9)) ([eba7532](https://github.com/CHIMEFRB/datatrail-cli/commit/eba7532f3a2c23854a62842f3ce54246916e0d6b))
* **ps-and-pull:** determination of common path ([a35bbad](https://github.com/CHIMEFRB/datatrail-cli/commit/a35bbad705b9702812281539516e2c7081a9516e)), closes [#19](https://github.com/CHIMEFRB/datatrail-cli/issues/19)
* **ps.py:** added error handling for returned strings ([#79](https://github.com/CHIMEFRB/datatrail-cli/issues/79)) ([0b3c5b6](https://github.com/CHIMEFRB/datatrail-cli/commit/0b3c5b6f95da361c080534f0e34132172300b956))
* **ps:** belongs_to cannot be none must be empty string ([#69](https://github.com/CHIMEFRB/datatrail-cli/issues/69)) ([b348dbd](https://github.com/CHIMEFRB/datatrail-cli/commit/b348dbdaa94e106f9c55be006b572566155d2be6))
* **ps:** bug where common path was not the parent dir of file ([3ba1969](https://github.com/CHIMEFRB/datatrail-cli/commit/3ba1969fec4aa5a57e5913a74d5d6aa10a7d86d7))
* **ps:** common path bug ([266cc3a](https://github.com/CHIMEFRB/datatrail-cli/commit/266cc3af3d3c397e83c9e18bad39ea5178b191f8))
* **ps:** controlled error if dataset doesnt exist in datatrail ([09a9d13](https://github.com/CHIMEFRB/datatrail-cli/commit/09a9d13a879971b65902ea19c3b2cda8ce7289de))
* **ps:** if parent dataset show only policies ([99b4bdd](https://github.com/CHIMEFRB/datatrail-cli/commit/99b4bddfbb788f6617dce408342232e0aa411156))
* **ps:** invalid scopes, valid scopes are now shown after error message ([5347137](https://github.com/CHIMEFRB/datatrail-cli/commit/534713782fe5105055506d55f1f43c51c110a4b4))
* **ps:** shows multiple larger datasets in belongs to ([6b32903](https://github.com/CHIMEFRB/datatrail-cli/commit/6b32903007a77f4d8539659870dacbcd94e67f18))
* **pull:** catch errors when no files at minoc ([fd34637](https://github.com/CHIMEFRB/datatrail-cli/commit/fd346373a3cdab93d0532a82cef5a8a04940aea7))
* **pull:** default directory ([da6a41d](https://github.com/CHIMEFRB/datatrail-cli/commit/da6a41d9c1dce3613996f735fef65ed62bbcc302))
* **pull:** FileNotFoundError stopping download ([#15](https://github.com/CHIMEFRB/datatrail-cli/issues/15)) ([cdee724](https://github.com/CHIMEFRB/datatrail-cli/commit/cdee7248d28a94c8bd4cabe3df9c93a337342dd3))
* **pull:** more processors than files bug ([0536326](https://github.com/CHIMEFRB/datatrail-cli/commit/053632632fd55cb5bba4fe7ce1d398148e0c9cba))
* **pull:** more processors than files bug ([e44bbe1](https://github.com/CHIMEFRB/datatrail-cli/commit/e44bbe1a14900f034f998b664c1d394fcf31c7a7)), closes [#147](https://github.com/CHIMEFRB/datatrail-cli/issues/147)
* **pull:** set group permissions if site is canfar ([70236ae](https://github.com/CHIMEFRB/datatrail-cli/commit/70236ae21c0e324d153be89dcead87489b77e5e5))
* **pull:** wrap download in tenacity retry ([ebdf5b1](https://github.com/CHIMEFRB/datatrail-cli/commit/ebdf5b10489b6a33937576850d57d05b1c1eefcb))
* **pull:** wrap download in tenacity retry ([8253157](https://github.com/CHIMEFRB/datatrail-cli/commit/8253157e78e1f0abb71fe71fb396b72d1ba51911))
* **scout:** change order of the args ([d5c33b8](https://github.com/CHIMEFRB/datatrail-cli/commit/d5c33b8ab8a5204fb63f1eb9744d1aa6d5c1f5d1))
* **scout:** change the order of the arguments ([c7ab294](https://github.com/CHIMEFRB/datatrail-cli/commit/c7ab29459707be153d12f1ff562cf46b984ed519))
* **scout:** improve error handling ([#87](https://github.com/CHIMEFRB/datatrail-cli/issues/87)) ([1937e9b](https://github.com/CHIMEFRB/datatrail-cli/commit/1937e9bbedfda0ab11919428b0b1b027900f594d))
* **test:** changed docstring expected in help test ([fed9342](https://github.com/CHIMEFRB/datatrail-cli/commit/fed9342df20b6843171a8cb4b288899ada74e261))
* **timeout:** bound every REST call with a request timeout ([fb533a2](https://github.com/CHIMEFRB/datatrail-cli/commit/fb533a2487c744fd18da4857b9ab74bea4615459))
* **unregistered:** improve pattern matching ([22ff11a](https://github.com/CHIMEFRB/datatrail-cli/commit/22ff11aa6d8aa390e465bf0ef62065f288f05bac))
* **unregistered:** improve way info displayed ([21e19a7](https://github.com/CHIMEFRB/datatrail-cli/commit/21e19a7ea239667ac882b1d8fbff57a145989227))
* **unregistered:** improve way info displayed ([c5f0fca](https://github.com/CHIMEFRB/datatrail-cli/commit/c5f0fca6f6f53e5004e1f1868517100572d68d1a))
* Update cadcdata to version 2.5 ([#58](https://github.com/CHIMEFRB/datatrail-cli/issues/58)) ([8ed6ad3](https://github.com/CHIMEFRB/datatrail-cli/commit/8ed6ad3914850483d147f0605809c1dd76363403))
* **version:** color ([ac2c7be](https://github.com/CHIMEFRB/datatrail-cli/commit/ac2c7bea886f48cc5fa5b84443999fb6e3809461))


### Documentation

* add unregistered command ([d8dd35b](https://github.com/CHIMEFRB/datatrail-cli/commit/d8dd35b22069b69ff7e3e76b6dc935696f8c2840))
* **all-docs:** revamp and additional content ([697fa6f](https://github.com/CHIMEFRB/datatrail-cli/commit/697fa6f2d2e150414c034c9d45a461808cd87381))
* **cli:** started docs ([f1838d5](https://github.com/CHIMEFRB/datatrail-cli/commit/f1838d5864cfed16e5221e9b5affaebb39ec108d))
* **gh-action:** build docs ([0698516](https://github.com/CHIMEFRB/datatrail-cli/commit/0698516e1670fb7a019ac271707d1d40fa4c5904))
* **gh-action:** install without dev ([0ea4a92](https://github.com/CHIMEFRB/datatrail-cli/commit/0ea4a92395c4eb04e6e6913679c3fd9b1b0cbd56))
* **gh-actions:** fix python version ([6db8c76](https://github.com/CHIMEFRB/datatrail-cli/commit/6db8c76298da316b7614d9ce794154ce75b83939))
* **index.md:** allow comments ([c680000](https://github.com/CHIMEFRB/datatrail-cli/commit/c6800007925c5794a5f7c29a63934c904cdaea07))
* **index:** add clear command ([01fcfb5](https://github.com/CHIMEFRB/datatrail-cli/commit/01fcfb5df89a8c567f743c26cc2342ccad93c632))
* **index:** badge ([09c637e](https://github.com/CHIMEFRB/datatrail-cli/commit/09c637eea007d0176a0ca0abe7524ca9f5c8a667))
* **index:** rewording ([6e7b2d1](https://github.com/CHIMEFRB/datatrail-cli/commit/6e7b2d1985233595374dc6d311b7b34389f92344))
* **index:** small fixes ([6483813](https://github.com/CHIMEFRB/datatrail-cli/commit/6483813033d71281a973dc52d250ae4e37a2df9e))
* **index:** update commands available ([aec676d](https://github.com/CHIMEFRB/datatrail-cli/commit/aec676d576082e288ee7144c39e34eb289dc8946))
* **index:** update install instructions ([fd7f51c](https://github.com/CHIMEFRB/datatrail-cli/commit/fd7f51c64d8f4b97f23d2b2b5897b34809a1bee3))
* **list:** test terminal plug in ([2cb4bc0](https://github.com/CHIMEFRB/datatrail-cli/commit/2cb4bc00ae89bdd1a7321ca2bd887da556225641))
* **README-and-index:** updated ([97353b3](https://github.com/CHIMEFRB/datatrail-cli/commit/97353b3c7f94a199363853b1622b930064ea085f))
* **scout:** added for new cli command ([be4f2bf](https://github.com/CHIMEFRB/datatrail-cli/commit/be4f2bfda25000b453b9696b2137e6bf0e8e4dd6))
* **scout:** reflect changes to cli in docs ([797eeac](https://github.com/CHIMEFRB/datatrail-cli/commit/797eeac4874619298c22f8f8a7623e079ac6542d))
* **scout:** typos ([7f633b1](https://github.com/CHIMEFRB/datatrail-cli/commit/7f633b17d514303d260990e1ece849d1c489ef91))
* **style:** use termynal ([e908d47](https://github.com/CHIMEFRB/datatrail-cli/commit/e908d4786e63972bef9f712b6c740088c8ac7906))
* update mkdocs config + ci/cd ([3a1014e](https://github.com/CHIMEFRB/datatrail-cli/commit/3a1014e75b0639f991cb49baf826bd925455b2f4))
* update mkdocs config + ci/cd ([0e4bee0](https://github.com/CHIMEFRB/datatrail-cli/commit/0e4bee0efbf9cd28fe4964497b5b0b7492efc3c2))
* **user-guide:** command highlights ([6813964](https://github.com/CHIMEFRB/datatrail-cli/commit/6813964e361391a8cbd4558b7c9bcda32c42cd7c))
* **user-guide:** completed ([a25ac76](https://github.com/CHIMEFRB/datatrail-cli/commit/a25ac767f8fee8bb22d100358481090c186f8e1f))

## [0.12.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.11.1...v0.12.0) (2026-08-24)


### Features

* **unregistered:** command to search for event in unregistered results bucket ([1bb4ca0](https://github.com/CHIMEFRB/datatrail-cli/commit/1bb4ca0c118e042a907f38205af5d7ed6bf9f16d))


### Documentation

* add unregistered command ([d8dd35b](https://github.com/CHIMEFRB/datatrail-cli/commit/d8dd35b22069b69ff7e3e76b6dc935696f8c2840))

## [0.11.1](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.11.0...v0.11.1) (2026-07-21)


### Bug Fixes

* **unregistered:** improve way info displayed ([c5f0fca](https://github.com/CHIMEFRB/datatrail-cli/commit/c5f0fca6f6f53e5004e1f1868517100572d68d1a))

## [0.11.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.10.3...v0.11.0) (2026-07-07)


### Features

* **ls & ps:** add --json flag for machine readable output ([c4742a0](https://github.com/CHIMEFRB/datatrail-cli/commit/c4742a0dfe43823ce8e68f21e26e146b90db958c)), closes [#159](https://github.com/CHIMEFRB/datatrail-cli/issues/159)

## [0.10.3](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.10.2...v0.10.3) (2026-05-19)


### Bug Fixes

* connection errors raise correct status exit code ([9b4d7bc](https://github.com/CHIMEFRB/datatrail-cli/commit/9b4d7bcc74c6a7c6954d965f8ab421ea6181b016))

## [0.10.2](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.10.1...v0.10.2) (2026-05-07)


### Bug Fixes

* **pull:** more processors than files bug ([e44bbe1](https://github.com/CHIMEFRB/datatrail-cli/commit/e44bbe1a14900f034f998b664c1d394fcf31c7a7)), closes [#147](https://github.com/CHIMEFRB/datatrail-cli/issues/147)

## [0.10.1](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.10.0...v0.10.1) (2026-03-02)


### Bug Fixes

* **cli:** canfar status checks ([7f9df34](https://github.com/CHIMEFRB/datatrail-cli/commit/7f9df349ceeebb1caa7c1c2582cd3d1c54e8ec09))

## [0.10.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.9.3...v0.10.0) (2026-02-20)


### Features

* **cli:** add unregistered command ([b33a6fa](https://github.com/CHIMEFRB/datatrail-cli/commit/b33a6fae57ff2bdad6c26f0ed5402994fdef7650))
* **pull:** check all files were downloaded ([bb1d8b6](https://github.com/CHIMEFRB/datatrail-cli/commit/bb1d8b64378fe80a27944f8eaccf6ce674ce17d0))


### Bug Fixes

* **cadcclient:** improve handling of stdout ([320d4df](https://github.com/CHIMEFRB/datatrail-cli/commit/320d4dfcdd194aa69f9236c84f21dbfb8690068b))
* **pull:** wrap download in tenacity retry ([8253157](https://github.com/CHIMEFRB/datatrail-cli/commit/8253157e78e1f0abb71fe71fb396b72d1ba51911))
* **unregistered:** improve pattern matching ([22ff11a](https://github.com/CHIMEFRB/datatrail-cli/commit/22ff11aa6d8aa390e465bf0ef62065f288f05bac))

## [0.9.3](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.9.2...v0.9.3) (2026-02-16)


### Bug Fixes

* **cadcclient:** more robust switching of stdout ([9c90315](https://github.com/CHIMEFRB/datatrail-cli/commit/9c9031595a9e13d6471e4b5e5edc548a4d1545ad))
* **ls:** other section for scopes that don't match list of sites ([0b50d79](https://github.com/CHIMEFRB/datatrail-cli/commit/0b50d790fbfb21fa0edb16eb945722189333a1c2))

## [0.9.2](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.9.1...v0.9.2) (2026-01-15)


### Bug Fixes

* **cli:** removed pkg resources deprecation warning ([2ab793d](https://github.com/CHIMEFRB/datatrail-cli/commit/2ab793d753badfd9a2c6aa53ed95010366437c3f))

## [0.9.1](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.9.0...v0.9.1) (2026-01-09)


### Bug Fixes

* **cli:** wrap version check in try except ([2fc9d31](https://github.com/CHIMEFRB/datatrail-cli/commit/2fc9d3169cc28e675c4cfce51aa142b1f22466c4))

## [0.9.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.8.0...v0.9.0) (2025-05-12)


### Features

* **pull:** allows specific files to be pulled by designating names or paths in a local config file ([d3cfb59](https://github.com/CHIMEFRB/datatrail-cli/commit/d3cfb59906fe4cb13c8f549e8c2b6499c32e663e))


### Bug Fixes

* **test:** changed docstring expected in help test ([fed9342](https://github.com/CHIMEFRB/datatrail-cli/commit/fed9342df20b6843171a8cb4b288899ada74e261))

## [0.8.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.7.2...v0.8.0) (2025-04-22)


### Features

* **scout:** generalised scout functionality to check for discrepancies between all sites, not just minoc ([f3f1005](https://github.com/CHIMEFRB/datatrail-cli/commit/f3f1005722c48d4ac020b65ed13d19f6bc0bbd48))


### Bug Fixes

* **clear:** reorganise file_paths manipulation logic ([80f0f2d](https://github.com/CHIMEFRB/datatrail-cli/commit/80f0f2d2bf3d9836eef16f9f6d3bed5f88c8ff05))


### Documentation

* update mkdocs config + ci/cd ([0e4bee0](https://github.com/CHIMEFRB/datatrail-cli/commit/0e4bee0efbf9cd28fe4964497b5b0b7492efc3c2))

## [0.7.2](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.7.1...v0.7.2) (2024-07-08)


### Bug Fixes

* **cli:** check for luskan status ([405a3c2](https://github.com/CHIMEFRB/datatrail-cli/commit/405a3c21334b5d8d96ab42436355d8c329880d74))

## [0.7.1](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.7.0...v0.7.1) (2024-06-25)


### Bug Fixes

* **cadcclient:** check canfar status ([484562c](https://github.com/CHIMEFRB/datatrail-cli/commit/484562c3c8345dd032c00923d3250c1be4a12191))
* **cli:** check minoc status ([6a0d6df](https://github.com/CHIMEFRB/datatrail-cli/commit/6a0d6dfc4f3490dc407c08d106d7740bb5d892e3))
* **scout:** change the order of the arguments ([c7ab294](https://github.com/CHIMEFRB/datatrail-cli/commit/c7ab29459707be153d12f1ff562cf46b984ed519))


### Documentation

* **scout:** reflect changes to cli in docs ([797eeac](https://github.com/CHIMEFRB/datatrail-cli/commit/797eeac4874619298c22f8f8a7623e079ac6542d))

## [0.7.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.6.1...v0.7.0) (2024-06-06)


### Features

* **scout:** able to heal missing minoc replicas ([bc3b52d](https://github.com/CHIMEFRB/datatrail-cli/commit/bc3b52d44fe7da7335279c96cec03e3deace6f9a))


### Documentation

* **scout:** added for new cli command ([be4f2bf](https://github.com/CHIMEFRB/datatrail-cli/commit/be4f2bfda25000b453b9696b2137e6bf0e8e4dd6))
* **scout:** typos ([7f633b1](https://github.com/CHIMEFRB/datatrail-cli/commit/7f633b17d514303d260990e1ece849d1c489ef91))

## [0.6.1](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.6.0...v0.6.1) (2024-06-04)


### Bug Fixes

* **scout:** improve error handling ([#87](https://github.com/CHIMEFRB/datatrail-cli/issues/87)) ([1937e9b](https://github.com/CHIMEFRB/datatrail-cli/commit/1937e9bbedfda0ab11919428b0b1b027900f594d))

## [0.6.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.5.7...v0.6.0) (2024-05-31)


### Features

* **scout:** add scout command to the cli ([#83](https://github.com/CHIMEFRB/datatrail-cli/issues/83)) ([5cb811f](https://github.com/CHIMEFRB/datatrail-cli/commit/5cb811f416c6fe099cf2405835ad867df125a62d))


### Bug Fixes

* **ps.py:** added error handling for returned strings ([#79](https://github.com/CHIMEFRB/datatrail-cli/issues/79)) ([0b3c5b6](https://github.com/CHIMEFRB/datatrail-cli/commit/0b3c5b6f95da361c080534f0e34132172300b956))

## [0.5.7](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.5.6...v0.5.7) (2024-05-10)


### Bug Fixes

* **functions:** changed return of find_missing_datasets to always ret… ([#76](https://github.com/CHIMEFRB/datatrail-cli/issues/76)) ([a8c0f3d](https://github.com/CHIMEFRB/datatrail-cli/commit/a8c0f3ded414c4e8d4fbca9529bfda7610531841))

## [0.5.6](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.5.5...v0.5.6) (2024-05-09)


### Bug Fixes

* **cli:** catch http 503 errors when validating scope ([b6e75af](https://github.com/CHIMEFRB/datatrail-cli/commit/b6e75affe6db6508882ed5e3da1b22bdec194156))
* **functions.py:** changed error catching checks to be for dictionaries with error keys in them as opposed to strings ([#74](https://github.com/CHIMEFRB/datatrail-cli/issues/74)) ([6fdb244](https://github.com/CHIMEFRB/datatrail-cli/commit/6fdb244e46a62253f4654681ec5e5d76431f49f0))

## [0.5.5](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.5.4...v0.5.5) (2024-05-01)


### Bug Fixes

* **ps:** belongs_to cannot be none must be empty string ([#69](https://github.com/CHIMEFRB/datatrail-cli/issues/69)) ([b348dbd](https://github.com/CHIMEFRB/datatrail-cli/commit/b348dbdaa94e106f9c55be006b572566155d2be6))

## [0.5.4](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.5.3...v0.5.4) (2024-04-24)


### Bug Fixes

* **functions.py:** added specific handling for canfar site, where the… ([#66](https://github.com/CHIMEFRB/datatrail-cli/issues/66)) ([895a3ca](https://github.com/CHIMEFRB/datatrail-cli/commit/895a3ca7bdb7000847313ef12fe17e50ad7308c8))

## [0.5.3](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.5.2...v0.5.3) (2024-04-24)


### Bug Fixes

* **functions.py:** patches deletion logic to check that the path to be deleted is greater than 3 levels deep ([#64](https://github.com/CHIMEFRB/datatrail-cli/issues/64)) ([ad43f35](https://github.com/CHIMEFRB/datatrail-cli/commit/ad43f35ce7b8fbc87210ca93df4433b3c4bbe06d))
* **ls:** seperate scopes by site ([5bddcc7](https://github.com/CHIMEFRB/datatrail-cli/commit/5bddcc7b368fa0594128f0f7fcb0b2e26959d77e))
* **ps:** shows multiple larger datasets in belongs to ([6b32903](https://github.com/CHIMEFRB/datatrail-cli/commit/6b32903007a77f4d8539659870dacbcd94e67f18))

## [0.5.2](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.5.1...v0.5.2) (2024-04-09)


### Bug Fixes

* Update cadcdata to version 2.5 ([#58](https://github.com/CHIMEFRB/datatrail-cli/issues/58)) ([8ed6ad3](https://github.com/CHIMEFRB/datatrail-cli/commit/8ed6ad3914850483d147f0605809c1dd76363403))

## [0.5.1](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.5.0...v0.5.1) (2024-01-09)


### Bug Fixes

* **init:** set valid choices for datatrail config init ([63f96c3](https://github.com/CHIMEFRB/datatrail-cli/commit/63f96c30c07be1d787381e5457021e805ea0cc6f))
* **pull:** set group permissions if site is canfar ([70236ae](https://github.com/CHIMEFRB/datatrail-cli/commit/70236ae21c0e324d153be89dcead87489b77e5e5))

## [0.5.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.4.4...v0.5.0) (2023-12-06)


### Features

* **ps:** if no files check if dataset is in unregistered bucket and notify user ([40ed903](https://github.com/CHIMEFRB/datatrail-cli/commit/40ed903623a4ec9fd4043b4d1863626303830a54)), closes [#46](https://github.com/CHIMEFRB/datatrail-cli/issues/46)


### Bug Fixes

* **ps:** controlled error if dataset doesnt exist in datatrail ([09a9d13](https://github.com/CHIMEFRB/datatrail-cli/commit/09a9d13a879971b65902ea19c3b2cda8ce7289de))

## [0.4.4](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.4.3...v0.4.4) (2023-09-19)


### Bug Fixes

* **ps:** if parent dataset show only policies ([99b4bdd](https://github.com/CHIMEFRB/datatrail-cli/commit/99b4bddfbb788f6617dce408342232e0aa411156))
* **ps:** invalid scopes, valid scopes are now shown after error message ([5347137](https://github.com/CHIMEFRB/datatrail-cli/commit/534713782fe5105055506d55f1f43c51c110a4b4))


### Documentation

* **all-docs:** revamp and additional content ([697fa6f](https://github.com/CHIMEFRB/datatrail-cli/commit/697fa6f2d2e150414c034c9d45a461808cd87381))
* **index.md:** allow comments ([c680000](https://github.com/CHIMEFRB/datatrail-cli/commit/c6800007925c5794a5f7c29a63934c904cdaea07))
* **index:** badge ([09c637e](https://github.com/CHIMEFRB/datatrail-cli/commit/09c637eea007d0176a0ca0abe7524ca9f5c8a667))
* **list:** test terminal plug in ([2cb4bc0](https://github.com/CHIMEFRB/datatrail-cli/commit/2cb4bc00ae89bdd1a7321ca2bd887da556225641))
* **style:** use termynal ([e908d47](https://github.com/CHIMEFRB/datatrail-cli/commit/e908d4786e63972bef9f712b6c740088c8ac7906))
* **user-guide:** command highlights ([6813964](https://github.com/CHIMEFRB/datatrail-cli/commit/6813964e361391a8cbd4558b7c9bcda32c42cd7c))
* **user-guide:** completed ([a25ac76](https://github.com/CHIMEFRB/datatrail-cli/commit/a25ac767f8fee8bb22d100358481090c186f8e1f))

## [0.4.3](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.4.2...v0.4.3) (2023-07-25)


### Documentation

* **index:** add clear command ([01fcfb5](https://github.com/CHIMEFRB/datatrail-cli/commit/01fcfb5df89a8c567f743c26cc2342ccad93c632))

## [0.4.2](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.4.1...v0.4.2) (2023-06-13)


### Bug Fixes

* **ps:** common path bug ([266cc3a](https://github.com/CHIMEFRB/datatrail-cli/commit/266cc3af3d3c397e83c9e18bad39ea5178b191f8))

## [0.4.1](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.4.0...v0.4.1) (2023-06-07)


### Bug Fixes

* **ps-and-pull:** determination of common path ([a35bbad](https://github.com/CHIMEFRB/datatrail-cli/commit/a35bbad705b9702812281539516e2c7081a9516e)), closes [#19](https://github.com/CHIMEFRB/datatrail-cli/issues/19)

## [0.4.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.3.0...v0.4.0) (2023-06-07)


### Features

* **clear:** remove empty parent dirs ([#20](https://github.com/CHIMEFRB/datatrail-cli/issues/20)) ([1559608](https://github.com/CHIMEFRB/datatrail-cli/commit/1559608de9d18d1b16a069c5b6b8136afb388fab))

## [0.3.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.2.0...v0.3.0) (2023-06-05)


### Features

* **clear:** command to unstage data locally or at arc ([#16](https://github.com/CHIMEFRB/datatrail-cli/issues/16)) ([737c781](https://github.com/CHIMEFRB/datatrail-cli/commit/737c7811a6112a46e842bc135d94d035a9bf301f))


### Bug Fixes

* **pull:** FileNotFoundError stopping download ([#15](https://github.com/CHIMEFRB/datatrail-cli/issues/15)) ([cdee724](https://github.com/CHIMEFRB/datatrail-cli/commit/cdee7248d28a94c8bd4cabe3df9c93a337342dd3))

## [0.2.0](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.1.2...v0.2.0) (2023-05-26)


### Features

* **cli:** check scope exists ([f14589b](https://github.com/CHIMEFRB/datatrail-cli/commit/f14589bc539ec3448348d1d6bc9b1b32d864d7ea))


### Bug Fixes

* **config.py:** typo ([#12](https://github.com/CHIMEFRB/datatrail-cli/issues/12)) ([279998b](https://github.com/CHIMEFRB/datatrail-cli/commit/279998bbc5a4c5bd9922db59b159a38fbfdade8b))
* **pull:** catch errors when no files at minoc ([fd34637](https://github.com/CHIMEFRB/datatrail-cli/commit/fd346373a3cdab93d0532a82cef5a8a04940aea7))

## [0.1.2](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.1.1...v0.1.2) (2023-05-24)


### Bug Fixes

* **ps-and-pull:** check if namespace already prepended ([#9](https://github.com/CHIMEFRB/datatrail-cli/issues/9)) ([eba7532](https://github.com/CHIMEFRB/datatrail-cli/commit/eba7532f3a2c23854a62842f3ce54246916e0d6b))

## [0.1.1](https://github.com/CHIMEFRB/datatrail-cli/compare/v0.1.0...v0.1.1) (2023-05-18)


### Bug Fixes

* **cli-test:** new test - marked as fix to trigger release ([aea98d0](https://github.com/CHIMEFRB/datatrail-cli/commit/aea98d07f63ee17f6d5b4acd396ea32e3aefbd11))

## 0.1.0 (2023-05-17)


### Features

* **cli:** aliases ([73ede83](https://github.com/CHIMEFRB/datatrail-cli/commit/73ede838133b54ef0ba8f45eda453547d601a180))
* **config:** added datatrail config module ([fe04ee1](https://github.com/CHIMEFRB/datatrail-cli/commit/fe04ee1af77e3d416c103e9ef73a7d79a4b616d5))
* **gh-actions:** ci and cd ([ebb7a96](https://github.com/CHIMEFRB/datatrail-cli/commit/ebb7a966836d2a4f57287191b9396d9b72cb3cfe))
* **ls,-pull:** partially implemented ([6689d11](https://github.com/CHIMEFRB/datatrail-cli/commit/6689d119782d1e251935050c508fb14969ff33d2))
* **ls,pull:** fully implemented ([2105f5a](https://github.com/CHIMEFRB/datatrail-cli/commit/2105f5a86dc42a0618903d0e315bc6490fd633ed))
* **ls:** option to write ls datasets to disk ([513d665](https://github.com/CHIMEFRB/datatrail-cli/commit/513d665a843bb4aa1f6f92e54ab020ee4f1477ab))
* **ls:** show datasets in given parent dataset ([15f7da1](https://github.com/CHIMEFRB/datatrail-cli/commit/15f7da1aa76a2a0c75f9229e445f96886b353a1f))
* **ls:** show larger datasets ([344e230](https://github.com/CHIMEFRB/datatrail-cli/commit/344e230f9798ad8a27752431bfd70f73370488f8))
* **project:** boilerplate added ([43085a1](https://github.com/CHIMEFRB/datatrail-cli/commit/43085a15789c2045ea41bca9aa89c26c26182019))
* **ps:** function implemented ([6feedde](https://github.com/CHIMEFRB/datatrail-cli/commit/6feedde08b0dddc3c9b43aba17999e681a2c6b1e))
* **ps:** show num files and size by default, flag to show all files ([cccbd33](https://github.com/CHIMEFRB/datatrail-cli/commit/cccbd3337289699f80112edff612abf746407f4b))
* **pull:** display size of files to be pulled before prompt ([38cffcc](https://github.com/CHIMEFRB/datatrail-cli/commit/38cffccb18dcaca41150ee7af85b4c80f6137284))
* **pull:** implemented multiprocessor pull ([2e7b332](https://github.com/CHIMEFRB/datatrail-cli/commit/2e7b33205789c54e4f9544223a0555d74edd464d))
* **structure:** added skeleton code ([c3e57f6](https://github.com/CHIMEFRB/datatrail-cli/commit/c3e57f63ea0e54c45f12a4c3682ed01e5d9489ec))


### Bug Fixes

* **cli:** updated some docs ([4a61228](https://github.com/CHIMEFRB/datatrail-cli/commit/4a61228300d5082e76081d84520fddf743cc0ebf))
* **functions:** bug ([f4e3788](https://github.com/CHIMEFRB/datatrail-cli/commit/f4e3788944e5a95f868e139369abdfac35c61caa))
* **ls:** show all larger datasets for scope ([cda63ac](https://github.com/CHIMEFRB/datatrail-cli/commit/cda63ac3053912aa0f4f0bc4781773e3ce46ac0a)), closes [#1](https://github.com/CHIMEFRB/datatrail-cli/issues/1)
* **ps:** bug where common path was not the parent dir of file ([3ba1969](https://github.com/CHIMEFRB/datatrail-cli/commit/3ba1969fec4aa5a57e5913a74d5d6aa10a7d86d7))
* **pull:** default directory ([da6a41d](https://github.com/CHIMEFRB/datatrail-cli/commit/da6a41d9c1dce3613996f735fef65ed62bbcc302))
* **version:** color ([ac2c7be](https://github.com/CHIMEFRB/datatrail-cli/commit/ac2c7bea886f48cc5fa5b84443999fb6e3809461))


### Documentation

* **cli:** started docs ([f1838d5](https://github.com/CHIMEFRB/datatrail-cli/commit/f1838d5864cfed16e5221e9b5affaebb39ec108d))
* **gh-action:** build docs ([0698516](https://github.com/CHIMEFRB/datatrail-cli/commit/0698516e1670fb7a019ac271707d1d40fa4c5904))
* **gh-action:** install without dev ([0ea4a92](https://github.com/CHIMEFRB/datatrail-cli/commit/0ea4a92395c4eb04e6e6913679c3fd9b1b0cbd56))
* **gh-actions:** fix python version ([6db8c76](https://github.com/CHIMEFRB/datatrail-cli/commit/6db8c76298da316b7614d9ce794154ce75b83939))
* **index:** rewording ([6e7b2d1](https://github.com/CHIMEFRB/datatrail-cli/commit/6e7b2d1985233595374dc6d311b7b34389f92344))
* **index:** small fixes ([6483813](https://github.com/CHIMEFRB/datatrail-cli/commit/6483813033d71281a973dc52d250ae4e37a2df9e))
* **index:** update commands available ([aec676d](https://github.com/CHIMEFRB/datatrail-cli/commit/aec676d576082e288ee7144c39e34eb289dc8946))
* **index:** update install instructions ([fd7f51c](https://github.com/CHIMEFRB/datatrail-cli/commit/fd7f51c64d8f4b97f23d2b2b5897b34809a1bee3))
* **README-and-index:** updated ([97353b3](https://github.com/CHIMEFRB/datatrail-cli/commit/97353b3c7f94a199363853b1622b930064ea085f))
