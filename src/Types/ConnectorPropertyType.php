<?php declare(strict_types = 1);

/**
 * ConnectorPropertyType.php
 *
 * @license        More in LICENSE.md
 * @copyright      https://www.fastybird.com
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Types
 * @since          0.19.0
 *
 * @date           10.02.22
 */

namespace FastyBird\FbBusConnector\Types;

use Consistence;
use FastyBird\Metadata\Types as MetadataTypes;

/**
 * Connector property name types
 *
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Types
 *
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 */
class ConnectorPropertyType extends Consistence\Enum\Enum
{

	/**
	 * Define device states
	 */
	public const NAME_BAUD_RATE = MetadataTypes\ConnectorPropertyIdentifierType::IDENTIFIER_BAUD_RATE;
	public const NAME_INTERFACE = MetadataTypes\ConnectorPropertyIdentifierType::IDENTIFIER_INTERFACE;
	public const NAME_ADDRESS = MetadataTypes\ConnectorPropertyIdentifierType::IDENTIFIER_ADDRESS;
	public const NAME_PROTOCOL = 'protocol';

	/**
	 * @return string
	 */
	public function __toString(): string
	{
		return strval(self::getValue());
	}

}
