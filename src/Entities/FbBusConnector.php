<?php declare(strict_types = 1);

/**
 * FbBusConnector.php
 *
 * @license        More in LICENSE.md
 * @copyright      https://www.fastybird.com
 * @author         Adam Kadlec <adam.kadlec@fastybird.com>
 * @package        FastyBird:FbBusConnector!
 * @subpackage     Entities
 * @since          0.4.0
 *
 * @date           23.01.22
 */

namespace FastyBird\FbBusConnector\Entities;

use Consistence\Doctrine\Enum\EnumAnnotation as Enum;
use Doctrine\ORM\Mapping as ORM;
use FastyBird\DevicesModule\Entities as DevicesModuleEntities;
use FastyBird\FbBusConnector\Types;
use IPub\DoctrineCrud\Mapping\Annotation as IPubDoctrine;

/**
 * @ORM\Entity
 */
class FbBusConnector extends DevicesModuleEntities\Connectors\Connector implements IFbBusConnector
{

	public const CONNECTOR_TYPE = 'fb-bus';

	/**
	 * @var int|null
	 * @IPubDoctrine\Crud(is="writable")
	 */
	protected ?int $address = null;

	/**
	 * @var string|null
	 * @IPubDoctrine\Crud(is="writable")
	 */
	protected ?string $interface = null;

	/**
	 * @var int|null
	 * @IPubDoctrine\Crud(is="writable")
	 */
	protected ?int $baudRate = null;

	/**
	 * @var Types\ProtocolVersionType|null
	 *
	 * @Enum(class=Types\ProtocolVersionType::class)
	 * @IPubDoctrine\Crud(is="writable")
	 */
	protected ?Types\ProtocolVersionType $protocol = null;

	/**
	 * {@inheritDoc}
	 */
	public function getType(): string
	{
		return self::CONNECTOR_TYPE;
	}

	/**
	 * {@inheritDoc}
	 */
	public function getAddress(): int
	{
		$address = $this->getParam('address', 254);

		return $address === null ? 254 : intval($address);
	}

	/**
	 * {@inheritDoc}
	 */
	public function setAddress(?int $address): void
	{
		$this->setParam('address', $address);
	}

	/**
	 * {@inheritDoc}
	 */
	public function getInterface(): string
	{
		$interface = $this->getParam('interface', '/dev/ttyAMA0');

		return $interface ?? '/dev/ttyAMA0';
	}

	/**
	 * {@inheritDoc}
	 */
	public function setinterface(?string $interface): void
	{
		$this->setParam('interface', $interface);
	}

	/**
	 * {@inheritDoc}
	 */
	public function getBaudRate(): int
	{
		$baudRate = $this->getParam('baud_rate', 38400);

		return $baudRate === null ? 38400 : intval($baudRate);
	}

	/**
	 * {@inheritDoc}
	 */
	public function setBaudRate(?int $baudRate): void
	{
		$this->setParam('baud_rate', $baudRate);
	}

	/**
	 * {@inheritDoc}
	 */
	public function getProtocol(): Types\ProtocolVersionType
	{
		$protocol = $this->getParam('protocol', Types\ProtocolVersionType::VERSION_1);

		return $protocol === null ? Types\ProtocolVersionType::get(Types\ProtocolVersionType::VERSION_1) : Types\ProtocolVersionType::get($protocol);
	}

	/**
	 * {@inheritDoc}
	 */
	public function setProtocol(?Types\ProtocolVersionType $protocol): void
	{
		$this->setParam('protocol', $protocol);
	}

	/**
	 * {@inheritDoc}
	 */
	public function toArray(): array
	{
		return array_merge(parent::toArray(), [
			'address'          => $this->getAddress(),
			'interface' => $this->getinterface(),
			'baud_rate'        => $this->getBaudRate(),
			'protocol'         => $this->getProtocol()->getValue(),
		]);
	}

	/**
	 * {@inheritDoc}
	 */
	public function getDiscriminatorName(): string
	{
		return self::CONNECTOR_TYPE;
	}

}
