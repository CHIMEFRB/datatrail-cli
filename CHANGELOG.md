# Changelog

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
