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
use FastyBird\Metadata\Types as MetadataTypes;

/**
 * @ORM\Entity
 */
class FbBusConnector extends DevicesModuleEntities\Connectors\Connector implements IFbBusConnector
{

	public const CONNECTOR_TYPE = 'fb-bus';

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
		$property = $this->findProperty(MetadataTypes\ConnectorPropertyNameType::NAME_ADDRESS);

		if (
			$property === null
			|| !$property instanceof DevicesModuleEntities\Connectors\Properties\IStaticProperty
			|| !is_int($property->getValue())
		) {
			return 254;
		}

		return $property->getValue();
	}

	/**
	 * {@inheritDoc}
	 */
	public function getInterface(): string
	{
		$property = $this->findProperty(MetadataTypes\ConnectorPropertyNameType::NAME_INTERFACE);

		if (
			$property === null
			|| !$property instanceof DevicesModuleEntities\Connectors\Properties\IStaticProperty
			|| !is_string($property->getValue())
		) {
			return '/dev/ttyAMA0';
		}

		return $property->getValue();
	}

	/**
	 * {@inheritDoc}
	 */
	public function getBaudRate(): int
	{
		$property = $this->findProperty(MetadataTypes\ConnectorPropertyNameType::NAME_BAUD_RATE);

		if (
			$property === null
			|| !$property instanceof DevicesModuleEntities\Connectors\Properties\IStaticProperty
			|| !is_int($property->getValue())
		) {
			return 38400;
		}

		return $property->getValue();
	}

	/**
	 * {@inheritDoc}
	 */
	public function getProtocol(): Types\ProtocolVersionType
	{
		$property = $this->findProperty(MetadataTypes\ConnectorPropertyNameType::NAME_BAUD_RATE);

		if (
			$property === null
			|| !$property instanceof DevicesModuleEntities\Connectors\Properties\IStaticProperty
			|| !is_numeric($property->getValue())
			|| !Types\ProtocolVersionType::isValidValue($property->getValue())
		) {
			return Types\ProtocolVersionType::get(Types\ProtocolVersionType::VERSION_1);
		}

		return Types\ProtocolVersionType::get($property->getValue());
	}

	/**
	 * {@inheritDoc}
	 */
	public function toArray(): array
	{
		return array_merge(parent::toArray(), [
			'address'   => $this->getAddress(),
			'interface' => $this->getinterface(),
			'baud_rate' => $this->getBaudRate(),
			'protocol'  => $this->getProtocol()->getValue(),
		]);
	}

	/**
	 * {@inheritDoc}
	 */
	public function getDiscriminatorName(): string
	{
		return self::CONNECTOR_TYPE;
	}

	/**
	 * {@inheritDoc}
	 */
	public function getSource()
	{
		return MetadataTypes\ConnectorSourceType::get(MetadataTypes\ConnectorSourceType::SOURCE_CONNECTOR_FB_BUS);
	}

}
