<?php declare(strict_types = 1);

/**
 * ProtocolVersionType.php
 *
 * @license        More in LICENSE.md
 * @copyright      https://www.fastybird.com
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Entities
 * @since          0.1.0
 *
 * @date           03.02.22
 */

namespace FastyBird\FbBusConnector\Types;

use Consistence;

/**
 * Protocol versions
 *
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Types
 *
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 */
class ProtocolVersionType extends Consistence\Enum\Enum
{

	/**
	 * Define states
	 */
	public const VERSION_1 = 0x01;

	/**
	 * @return string
	 */
	public function __toString(): string
	{
		return strval(self::getValue());
	}

}
