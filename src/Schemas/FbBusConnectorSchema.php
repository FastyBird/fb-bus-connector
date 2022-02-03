<?php declare(strict_types = 1);

/**
 * FbBusConnectorSchema.php
 *
 * @license        More in LICENSE.md
 * @copyright      https://www.fastybird.com
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Schemas
 * @since          0.4.0
 *
 * @date           23.01.22
 */

namespace FastyBird\FbBusConnector\Schemas;

use FastyBird\DevicesModule\Schemas as DevicesModuleSchemas;
use FastyBird\FbBusConnector\Entities;
use Neomerx\JsonApi;

/**
 * FastyBird BUS connector entity schema
 *
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Schemas
 *
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 *
 * @phpstan-extends DevicesModuleSchemas\Connectors\ConnectorSchema<Entities\IFbBusConnector>
 */
final class FbBusConnectorSchema extends DevicesModuleSchemas\Connectors\ConnectorSchema
{

	/**
	 * Define entity schema type string
	 */
	public const SCHEMA_TYPE = 'devices-module/connector-fb-bus';

	/**
	 * {@inheritDoc}
	 */
	public function getEntityClass(): string
	{
		return Entities\FbBusConnector::class;
	}

	/**
	 * @return string
	 */
	public function getType(): string
	{
		return self::SCHEMA_TYPE;
	}

	/**
	 * @param Entities\IFbBusConnector $connector
	 * @param JsonApi\Contracts\Schema\ContextInterface $context
	 *
	 * @return iterable<string, mixed>
	 *
	 * @phpcsSuppress SlevomatCodingStandard.TypeHints.TypeHintDeclaration.MissingParameterTypeHint
	 */
	public function getAttributes($connector, JsonApi\Contracts\Schema\ContextInterface $context): iterable
	{
		return array_merge((array) parent::getAttributes($connector, $context), [
			'address'   => $connector->getAddress(),
			'interface' => $connector->getInterface(),
			'baud_rate' => $connector->getBaudRate(),
			'protocol'  => $connector->getProtocol()->getValue(),
		]);
	}

}
