<?php declare(strict_types = 1);

/**
 * FbBusConnectorExtension.php
 *
 * @license        More in license.md
 * @copyright      https://www.fastybird.com
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 * @package        FastyBird:FbBusConnector!
 * @subpackage     DI
 * @since          0.4.0
 *
 * @date           23.01.22
 */

namespace FastyBird\FbBusConnector\DI;

use Doctrine\Persistence;
use FastyBird\FbBusConnector\Hydrators;
use FastyBird\FbBusConnector\Schemas;
use Nette;
use Nette\DI;

/**
 * FastyBird BUS connector
 *
 * @package        FastyBird:FbBusConnector!
 * @subpackage     DI
 *
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 */
class FbBusConnectorExtension extends DI\CompilerExtension
{

	/**
	 * @param Nette\Configurator $config
	 * @param string $extensionName
	 *
	 * @return void
	 */
	public static function register(
		Nette\Configurator $config,
		string $extensionName = 'fbFbBusConnector'
	): void {
		$config->onCompile[] = function (
			Nette\Configurator $config,
			DI\Compiler $compiler
		) use ($extensionName): void {
			$compiler->addExtension($extensionName, new FbBusConnectorExtension());
		};
	}

	/**
	 * {@inheritDoc}
	 */
	public function loadConfiguration(): void
	{
		$builder = $this->getContainerBuilder();

		// API schemas
		$builder->addDefinition($this->prefix('schemas.connector.fbBus'), new DI\Definitions\ServiceDefinition())
			->setType(Schemas\FbBusConnectorSchema::class);

		$builder->addDefinition($this->prefix('schemas.device.fbBus'), new DI\Definitions\ServiceDefinition())
			->setType(Schemas\FbBusDeviceSchema::class);

		// API hydrators
		$builder->addDefinition($this->prefix('hydrators.connector.fbBus'), new DI\Definitions\ServiceDefinition())
			->setType(Hydrators\FbBusConnectorHydrator::class);

		$builder->addDefinition($this->prefix('hydrators.device.fbBus'), new DI\Definitions\ServiceDefinition())
			->setType(Hydrators\FbBusDeviceHydrator::class);
	}

	/**
	 * {@inheritDoc}
	 */
	public function beforeCompile(): void
	{
		parent::beforeCompile();

		$builder = $this->getContainerBuilder();

		/**
		 * Doctrine entities
		 */

		$ormAnnotationDriverService = $builder->getDefinition('nettrineOrmAnnotations.annotationDriver');

		if ($ormAnnotationDriverService instanceof DI\Definitions\ServiceDefinition) {
			$ormAnnotationDriverService->addSetup('addPaths', [[__DIR__ . DIRECTORY_SEPARATOR . '..' . DIRECTORY_SEPARATOR . 'Entities']]);
		}

		$ormAnnotationDriverChainService = $builder->getDefinitionByType(Persistence\Mapping\Driver\MappingDriverChain::class);

		if ($ormAnnotationDriverChainService instanceof DI\Definitions\ServiceDefinition) {
			$ormAnnotationDriverChainService->addSetup('addDriver', [
				$ormAnnotationDriverService,
				'FastyBird\FbBusConnector\Entities',
			]);
		}
	}

}
