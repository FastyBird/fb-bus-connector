<?php declare(strict_types = 1);

namespace Tests\Cases;

use FastyBird\FbBusConnector\DI;
use FastyBird\FbBusConnector\Hydrators;
use FastyBird\FbBusConnector\Schemas;
use Nette;
use Ninjify\Nunjuck\TestCase\BaseTestCase;
use Tester\Assert;

require_once __DIR__ . '/../../../bootstrap.php';

/**
 * @testCase
 */
final class ServicesTest extends BaseTestCase
{

	public function testServicesRegistration(): void
	{
		$container = $this->createContainer();

		Assert::notNull($container->getByType(Schemas\FbBusDeviceSchema::class));
		Assert::notNull($container->getByType(Schemas\FbBusConnectorSchema::class));

		Assert::notNull($container->getByType(Hydrators\FbBusDeviceHydrator::class));
		Assert::notNull($container->getByType(Hydrators\FbBusConnectorHydrator::class));
	}

	/**
	 * @return Nette\DI\Container
	 */
	protected function createContainer(): Nette\DI\Container
	{
		$rootDir = __DIR__ . '/../../../';

		$config = new Nette\Configurator();
		$config->setTempDirectory(TEMP_DIR);

		$config->addParameters(['container' => ['class' => 'SystemContainer_' . md5((string) time())]]);
		$config->addParameters(['appDir' => $rootDir, 'wwwDir' => $rootDir]);

		$config->addConfig(__DIR__ . '/../../../common.neon');

		DI\FbBusConnectorExtension::register($config);

		return $config->createContainer();
	}

}

$test_case = new ServicesTest();
$test_case->run();
